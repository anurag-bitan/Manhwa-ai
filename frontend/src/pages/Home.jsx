/* FULL FIXED Home.jsx — UI same as original, preview + polling added */

import React, { useState, useRef, useEffect } from "react";
import {
  Upload,
  Play,
  Download,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  Settings,
  Sparkles,
  Lock,
} from "lucide-react";

// ⭐ Uses .env API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const Home = () => {
  const [file, setFile] = useState(null);
  const [mangaName, setMangaName] = useState("");
  const [mode, setMode] = useState("images");
  const [previewUrl, setPreviewUrl] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);

  // ⭐ job_id added for polling
  const [jobId, setJobId] = useState(null);

  const [settings, setSettings] = useState({
    frameDuration: 3,
    resolution: "1080p",
  });

  const fileInputRef = useRef(null);

  // ----------------------------------------------------------------------
  // ⭐ Poll backend every 3 seconds until final video is ready
  // ----------------------------------------------------------------------
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/video_status/${jobId}`);
        if (!res.ok) return;

        const data = await res.json();

        if (data.status === "completed") {
          setVideoUrl(data.video_url);
          setIsGenerating(false);
          setProgress(100);
          clearInterval(interval);
        }

        if (data.status === "error") {
          setError(data.message || "Video generation failed.");
          setIsGenerating(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Status polling error:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobId]);
  // ----------------------------------------------------------------------

  const validateFile = (fileToValidate) => {
    if (!fileToValidate) return false;
    if (!fileToValidate.type.includes("pdf")) {
      setError("Please upload a PDF file");
      return false;
    }
    if (fileToValidate.size > 50 * 1024 * 1024) {
      setError("File size must be less than 50MB");
      return false;
    }
    setError(null);
    return true;
  };

  const handleFile = (selectedFile) => {
    if (validateFile(selectedFile)) {
      setFile(selectedFile);
      setVideoUrl(null);
      setPreviewUrl(null);
      setShowPreview(false);
      const nameWithoutExtension = selectedFile.name
        .split(".")
        .slice(0, -1)
        .join(".");
      setMangaName(nameWithoutExtension || "Untitled Manga");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const removeFile = () => {
    setFile(null);
    setMangaName("");
    setVideoUrl(null);
    setPreviewUrl(null);
    setShowPreview(false);
    setError(null);
    setProgress(0);
    setJobId(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ----------------------------------------------------------------------
  // ⭐ The main 2-step process (audio → preview+job → polling)
  // ----------------------------------------------------------------------
  const handleCreateVideo = async () => {
    if (!file) {
      setError("Please upload a manga PDF first");
      return;
    }

    setIsGenerating(true);
    setProgress(0);
    setError(null);
    setVideoUrl(null);
    setPreviewUrl(null);
    setShowPreview(false);

    try {
      setProgress(10);

      // ------------------------------------------------------------
      // 1. SEND PDF → generate_audio_story
      // ------------------------------------------------------------
      const formData = new FormData();
      formData.append("manga_pdf", file);
      formData.append("manga_name", mangaName);
      formData.append("manga_genre", "Action");

      const audioStoryResponse = await fetch(
        `${API_BASE_URL}/api/v1/generate_audio_story`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!audioStoryResponse.ok) {
        const errData = await audioStoryResponse.json();
        throw new Error(
          errData.detail || "Backend error during audio/story generation."
        );
      }

      const audioStoryData = await audioStoryResponse.json();
      console.log("Audio Story Response:", audioStoryData);

      setProgress(40);

      // ------------------------------------------------------------
      // 2. Request backend to generate_preview & start full render
      // ------------------------------------------------------------
      const videoResponse = await fetch(
        `${API_BASE_URL}/api/v1/generate_video`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(audioStoryData),
        }
      );

      if (!videoResponse.ok) {
        const errData = await videoResponse.json();
        throw new Error(
          errData.detail || "Backend error during final video generation."
        );
      }

      const videoData = await videoResponse.json();
      console.log("Video Generation Response:", videoData);

      // ⭐ Store preview + job_id
      setPreviewUrl(videoData.preview_url);
      setJobId(videoData.job_id);
      setShowPreview(true);

      setProgress(70);

      // optional auto-hide preview
      setTimeout(() => setShowPreview(false), 3000);
    } catch (err) {
      console.error("Error generating video:", err);
      setError(
        err.message || "Unknown error. Please check console."
      );
      setIsGenerating(false);
      setProgress(0);
    }
  };
  // ----------------------------------------------------------------------

  const formatSize = (bytes) => {
    if (!bytes) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const modes = [
    { value: "images", label: "Original Images", desc: "Use manga pages as-is", disabled: false },
    { value: "ai", label: "AI Enhanced", desc: "Apply AI improvements", disabled: true },
    { value: "both", label: "Hybrid Mode", desc: "Mix original & AI", disabled: true },
  ];

  const features = [
    { icon: "🎨", title: "AI Enhancement", desc: "Upscale and improve manga quality" },
    { icon: "✨", title: "Smart Transitions", desc: "Smooth animations between panels" },
    { icon: "🎵", title: "Custom Audio", desc: "Add background music and effects" },
  ];

  const VideoSkeleton = () => (
    <div className="w-full aspect-video bg-gray-800/50 rounded-xl overflow-hidden relative animate-pulse">
      <div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-gray-700/50 to-transparent animate-shimmer"
        style={{ backgroundSize: "200% 100%", animation: "shimmer 2s infinite" }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-purple-400 animate-spin" />
      </div>
    </div>
  );

  // ----------------------------------------------------------------------
  // ⭐ BELOW: FULL ORIGINAL UI (unchanged)
  // ----------------------------------------------------------------------

  return (
    <main className="relative min-h-screen bg-black text-white px-4 sm:px-6 lg:px-8 py-4 sm:py-8 overflow-hidden">
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>

      {/* BACKGROUND EFFECTS */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-48 sm:w-72 md:w-96 h-48 sm:h-72 md:h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-48 sm:w-72 md:w-96 h-48 sm:h-72 md:h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 left-1/2 w-48 sm:w-72 md:w-96 h-48 sm:h-72 md:h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
      </div>

      {/* MAIN CONTENT */}
      <div className="relative max-w-6xl mx-auto">
        {/* TITLE */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400">
            マンファ.ai
          </h1>
          <p className="text-gray-300 text-sm sm:text-base md:text-lg max-w-2xl mx-auto px-4">
            Transform your favorite manga into stunning videos with AI-powered transitions 
          </p>
        </div>

        {/* UPLOAD AREA — unchanged */}
        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="lg:col-span-2">
            <div
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
              className={`relative border-2 border-dashed rounded-xl sm:rounded-2xl p-4 sm:p-6 md:p-8 transition-all duration-300 ${
                isDragging ? "border-pink-500 bg-pink-500/10 scale-105" :
                file ? "border-green-500 bg-green-500/5" : "border-gray-600 bg-gray-800/30"
              } backdrop-blur-xl hover:border-purple-500 cursor-pointer group`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                onChange={(e) => handleFile(e.target.files[0])}
              />
              
              {!file ? (
                <div className="flex flex-col items-center justify-center py-6 sm:py-8">
                  <Upload className="w-12 h-12 sm:w-16 sm:h-16 text-purple-400 mb-3 sm:mb-4 group-hover:scale-110 transition-transform" />
                  <p className="text-lg sm:text-xl font-semibold text-gray-200 mb-2 text-center px-2">Drop your manga PDF here</p>
                  <p className="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-4">or click to browse files</p>
                  <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 text-xs text-gray-500 text-center">
                    <span>• PDF format only</span>
                    <span>• Max 50MB</span>
                    <span className="hidden sm:inline">• High quality recommended</span>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3 sm:gap-4">
                  <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-green-400" />
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className="font-semibold text-white truncate mb-1 text-sm sm:text-base">{file.name}</p>
                    <p className="text-xs sm:text-sm text-gray-400">{formatSize(file.size)}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-green-400" />
                      <span className="text-xs sm:text-sm text-green-400">Ready to convert</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(); }}
                    className="flex-shrink-0 p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 sm:w-5 sm:h-5 text-red-400" />
                  </button>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 p-3 sm:p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                <p className="text-red-300 text-xs sm:text-sm">{error}</p>
              </div>
            )}
          </div>

          {/* SETTINGS — unchanged */}
          <div className="bg-gray-800/30 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/30">
            <div className="flex items-center gap-2 mb-4 sm:mb-6">
              <Settings className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
              <h3 className="text-lg sm:text-xl font-semibold">Settings</h3>
            </div>

            <div className="mb-4 sm:mb-6">
              <label className="block text-xs sm:text-sm font-medium text-gray-300 mb-2 sm:mb-3">Generation Mode</label>
              <div className="space-y-2">
                {[
                  { value: "images", label: "Original Images", desc: "Use manga pages as-is", disabled: false },
                  { value: "ai", label: "AI Enhanced", desc: "Under Development", disabled: true },
                  { value: "both", label: "Hybrid", desc: "Under Development", disabled: true },
                ].map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-start p-2 sm:p-3 rounded-lg sm:rounded-xl transition-all relative ${
                      option.disabled
                        ? "bg-gray-800/20 border-2 border-gray-700/30 cursor-not-allowed opacity-60"
                        : mode === option.value
                        ? "bg-purple-500/20 border-2 border-purple-500 cursor-pointer"
                        : "bg-gray-800/40 border-2 border-gray-600/30 hover:bg-gray-700/40 cursor-pointer"
                    }`}
                  >
                    <input
                      type="radio"
                      name="mode"
                      value={option.value}
                      checked={mode === option.value}
                      onChange={(e) => !option.disabled && setMode(e.target.value)}
                      disabled={option.disabled}
                      className="mt-1 mr-2 sm:mr-3 cursor-pointer disabled:cursor-not-allowed"
                    />
                    <div className="flex-grow">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm sm:text-base">{option.label}</span>
                        {option.disabled && (
                          <Lock className="w-3 h-3 sm:w-4 sm:h-4 text-gray-400" />
                        )}
                      </div>
                      <div className="text-xs text-gray-400">
                        {option.disabled ? "Under Development" : option.desc}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* GENERATE BUTTON */}
        <div className="flex justify-center mb-6 sm:mb-8">
          <button
            onClick={handleCreateVideo}
            disabled={isGenerating || !file}
            className={`relative px-6 sm:px-8 md:px-12 py-3 sm:py-4 rounded-full font-bold text-sm sm:text-base md:text-lg transition-all duration-300 flex items-center gap-2 sm:gap-3 ${
              isGenerating || !file
                ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                : "bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 hover:shadow-2xl hover:shadow-purple-500/50 hover:scale-105 active:scale-95"
            }`}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 sm:w-6 sm:h-6 animate-spin" />
                <span className="hidden sm:inline">Generating Video...</span>
                <span className="sm:hidden">Generating...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5 sm:w-6 sm:h-6" />
                Generate Video
              </>
            )}
          </button>
        </div>

        {/* PREVIEW SECTION (5 seconds) */}
        {showPreview && previewUrl && (
          <div className="max-w-4xl mx-auto mb-6 sm:mb-8">
            <div className="bg-gray-800/30 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/30">
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
                <h3 className="text-lg sm:text-xl font-bold">Preview (5s)</h3>
              </div>
              <video autoPlay muted className="w-full rounded-lg sm:rounded-xl shadow-2xl">
                <source src={previewUrl} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        )}

        {/* SKELETON WHILE GENERATING */}
        {isGenerating && (
          <div className="max-w-2xl mx-auto mb-6 sm:mb-8">
            <div className="bg-gray-800/30 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/30">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs sm:text-sm font-medium text-gray-300">Processing...</span>
                <span className="text-xs sm:text-sm font-bold text-purple-400">{progress}%</span>
              </div>
              <div className="w-full h-2 sm:h-3 bg-gray-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 transition-all duration-500 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-4 sm:mt-6">
                <VideoSkeleton />
                <p className="text-center text-xs sm:text-sm text-gray-400 mt-3 sm:mt-4">
                  Creating your amazing video... This may take a few minutes
                </p>
              </div>
            </div>
          </div>
        )}

        {/* FINAL VIDEO */}
        {videoUrl && !isGenerating && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800/30 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/30">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0 mb-4">
                <h3 className="text-xl sm:text-2xl font-bold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-green-400" />
                  Video Ready!
                </h3>
                <a
                  href={videoUrl}
                  download={`${mangaName || 'manga-video'}.mp4`}
                  className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 hover:shadow-lg hover:shadow-green-500/50 transition-all font-semibold text-sm sm:text-base flex items-center justify-center gap-2 hover:scale-105 active:scale-95"
                >
                  <Download className="w-4 h-4 sm:w-5 sm:h-5" />
                  Download
                </a>
              </div>
              <video key={videoUrl} controls className="w-full rounded-lg sm:rounded-xl shadow-2xl">
                <source src={videoUrl} type="video/mp4" />
              </video>
              <div className="mt-4 flex flex-wrap gap-2 sm:gap-3 text-xs sm:text-sm text-gray-400">
                <span>• Mode: {mode}</span>
                <span>• Resolution: {settings.resolution}</span>
                <span>• Duration: ~{settings.frameDuration}s per frame</span>
              </div>
            </div>
          </div>
        )}

        {/* FEATURES SECTION */}
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mt-12 sm:mt-16 max-w-5xl mx-auto">
          {features.map((feature, i) => (
            <div
              key={i}
              className="bg-gray-800/30 backdrop-blur-xl rounded-xl sm:rounded-2xl p-6 border border-purple-500/30 hover:border-purple-500/60 transition-colors flex flex-col items-center text-center"
            >
              <div className="text-3xl sm:text-4xl mb-3">{feature.icon}</div>
              <h4 className="font-bold text-lg mb-2">{feature.title}</h4>
              <p className="text-gray-400 text-sm">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
};

export default Home;
