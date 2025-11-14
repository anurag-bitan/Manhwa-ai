import React, { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FaArrowRight } from "react-icons/fa";


const Landing = () => {
  const [videoEnded, setVideoEnded] = useState(false);

  const handleVideoEnd = () => {
    setVideoEnded(true);
  };

  return (
    <main className="relative min-h-screen bg-black overflow-hidden flex flex-col items-center justify-center text-center text-white px-4 sm:px-6 md:px-8">

      {/* Background - Full Black */}
      <div className="absolute inset-0 bg-black -z-20" />

      {/* Video Player */}
      <div className="absolute inset-0 w-full h-full overflow-hidden z-0">
        <video
          autoPlay
          muted
          playsInline
          onEnded={handleVideoEnd}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full object-cover"
          style={{
            minWidth: '100%',
            minHeight: '100%',
          }}
        >
          <source src="/270562.mp4" type="video/mp4" />
        </video>
      </div>

      

      {/* Content - Only visible after video ends */}
      {videoEnded && (
        <div className="relative z-10 mt-60 px-4 sm:px-6 md:px-8 w-full max-w-4xl mx-auto">
          

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.4, delay: 0.3 }}
            className="mt-6 sm:mt-8 md:mt-10"
          >
            <Link
              to="/home"
              className="group relative inline-flex items-center gap-2 px-5 sm:px-6 md:px-8 py-2.5 sm:py-3 md:py-4 rounded-full bg-gradient-to-r from-pink-500 to-purple-600 hover:scale-105 active:scale-95 transition-transform shadow-lg text-sm sm:text-base md:text-lg font-semibold"
            >
              <span>Get Started</span>
              <FaArrowRight className="transition-transform group-hover:translate-x-1" />
            </Link>
          </motion.div>
        </div>
      )}

    </main>
  );
};

export default Landing;