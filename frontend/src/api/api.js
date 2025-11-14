// ---------------------------------------------------------
// API CONFIG
// ---------------------------------------------------------

// Fallback to localhost if .env missing
const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Simple helper for consistent error parsing
async function parseJSONResponse(response) {
  try {
    return await response.json();
  } catch (err) {
    // Backend may return HTML on failure → avoid JSON parse crash
    const text = await response.text();
    throw new Error(
      `Backend returned non-JSON response (${response.status}):\n${text}`
    );
  }
}

// Optional retry wrapper (free, lightweight)
async function fetchWithRetry(url, options, retries = 1) {
  try {
    return await fetch(url, options);
  } catch (err) {
    if (retries > 0) {
      console.warn("Retrying request due to network error...");
      return fetchWithRetry(url, options, retries - 1);
    }
    throw err;
  }
}

// ---------------------------------------------------------
// 1. Generate Audio Story (PDF → OCR → Script)
// ---------------------------------------------------------

export const generateAudioStory = async (formData) => {
  const controller = new AbortController();

  // Abort after 10 minutes (PDF + TTS)
  const timeout = setTimeout(() => controller.abort(), 10 * 60 * 1000);

  try {
    const response = await fetchWithRetry(
      `${API_URL}/api/v1/generate_audio_story`,
      {
        method: "POST",
        body: formData,
        signal: controller.signal,
      }
    );

    clearTimeout(timeout);

    if (!response.ok) {
      const errorData = await parseJSONResponse(response);
      throw new Error(errorData.message || "Audio story failed.");
    }

    return await parseJSONResponse(response);
  } catch (err) {
    clearTimeout(timeout);
    throw err;
  }
};

// ---------------------------------------------------------
// 2. Generate Video (Fast 5s Preview + Background Render)
// ---------------------------------------------------------

export const generateVideo = async (storyData, preview = false) => {
  if (!storyData || typeof storyData !== "object") {
    throw new Error("Invalid storyData passed to generateVideo().");
  }

  const controller = new AbortController();

  // Video generation is long → abort after 25 minutes
  const timeout = setTimeout(() => controller.abort(), 25 * 60 * 1000);

  // Preview mode → shorter timeout
  if (preview) {
    clearTimeout(timeout);
    setTimeout(() => controller.abort(), 2 * 60 * 1000);
  }

  try {
    const response = await fetchWithRetry(
      `${API_URL}/api/v1/generate_video${preview ? "?preview=true" : ""}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(storyData),
        signal: controller.signal,
      }
    );

    clearTimeout(timeout);

    if (!response.ok) {
      const errorData = await parseJSONResponse(response);
      throw new Error(errorData.message || "Video generation failed.");
    }

    return await parseJSONResponse(response);
  } catch (err) {
    clearTimeout(timeout);
    throw err;
  }
};

// ---------------------------------------------------------
// 3. NEW — Poll video status (Final video finished?)
// ---------------------------------------------------------

export const getVideoStatus = async (jobId) => {
  if (!jobId) throw new Error("Job ID missing for getVideoStatus().");

  const response = await fetchWithRetry(
    `${API_URL}/api/v1/video_status/${jobId}`,
    { method: "GET" }
  );

  if (!response.ok) {
    const errorData = await parseJSONResponse(response);
    throw new Error(errorData.message || "Failed to fetch video status.");
  }

  return await parseJSONResponse(response);
};
