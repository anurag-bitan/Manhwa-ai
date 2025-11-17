// ---------------------------------------------------------
// API CONFIG
// ---------------------------------------------------------

const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseJSONResponse(response) {
  try {
    return await response.json();
  } catch {
    const text = await response.text();
    throw new Error(`Backend returned non-JSON (${response.status}):\n${text}`);
  }
}

async function fetchWithRetry(url, options, retries = 1) {
  try {
    return await fetch(url, options);
  } catch (err) {
    if (retries > 0) return fetchWithRetry(url, options, retries - 1);
    throw err;
  }
}

// Normalize backend response (image_urls / panel_images)
function normalizeStoryData(data) {
  const imageList = data.image_urls || data.panel_images || [];
  return {
    ...data,
    image_urls: Array.isArray(imageList) ? imageList : [],
  };
}

// ---------------------------------------------------------
// 1. Generate Audio Story
// ---------------------------------------------------------

export const generateAudioStory = async (formData) => {
  const response = await fetchWithRetry(
    `${API_URL}/generate_audio_story`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) throw await parseJSONResponse(response);

  const data = await parseJSONResponse(response);
  return normalizeStoryData(data);
};

// ---------------------------------------------------------
// 2. Generate Video
// ---------------------------------------------------------

export const generateVideo = async (storyData) => {
  const response = await fetchWithRetry(`${API_URL}/generate_video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(storyData),
  });

  if (!response.ok) throw await parseJSONResponse(response);

  return await parseJSONResponse(response);
};

// ---------------------------------------------------------
// 3. Correct Polling Endpoint
// ---------------------------------------------------------

export const getVideoStatus = async (jobId) => {
  if (!jobId) throw new Error("Job ID missing");

  const response = await fetchWithRetry(
    `${API_URL}/video_status/${jobId}`,
    {
      method: "GET",
    }
  );

  if (!response.ok) throw await parseJSONResponse(response);

  return await parseJSONResponse(response);
};
