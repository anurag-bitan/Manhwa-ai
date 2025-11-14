import React from "react";
import { Link } from "react-router-dom";
import { FaGithub, FaTwitter, FaYoutube, FaDiscord } from "react-icons/fa";

const Footer = () => {
  return (
    <footer className="relative bg-black text-white overflow-hidden">
      {/* Premium subtle shine effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] via-transparent to-transparent pointer-events-none"></div>

      <div className="relative max-w-7xl mx-auto px-6 py-16 lg:py-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-16">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity duration-300">
              <svg 
                width="32" 
                height="32" 
                viewBox="0 0 32 32" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
                className="flex-shrink-0"
              >
                {/* Simple AI symbol - play button in circle */}
                <circle cx="16" cy="16" r="14" stroke="white" strokeWidth="2" />
                <path d="M13 10L22 16L13 22V10Z" stroke="white" strokeWidth="2" strokeLinejoin="round" fill="none" />
              </svg>
              <h2 className="text-2xl font-bold tracking-tight">
                Manhwa.ai
              </h2>
            </Link>
            <p className="mt-5 text-sm font-semibold text-gray-400 leading-relaxed max-w-xs font-light">
              Transform your favorite manga into stunning videos with
              AI-powered technology for professional Anime-inspired content
              creation.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-5 tracking-wider uppercase">
              Quick Links
            </h3>
            <ul className="space-y-3.5">
              <li>
                <Link
                  to="/"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  Home
                </Link>
              </li>
              <li>
                <Link
                  to="/about"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  About
                </Link>
              </li>
              <li>
                <Link
                  to="/upload"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  Upload Manga
                </Link>
              </li>
              <li>
                <Link
                  to="/contact"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-5 tracking-wider uppercase">
              Resources
            </h3>
            <ul className="space-y-3.5">
              <li>
                <Link
                  to="/faq"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  FAQ
                </Link>
              </li>
              <li>
                <Link
                  to="/docs"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  Documentation
                </Link>
              </li>
              <li>
                <Link
                  to="/terms"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link
                  to="/privacy"
                  className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-300 inline-block font-light"
                >
                  Privacy Policy
                </Link>
              </li>
            </ul>
          </div>

          {/* Newsletter + Socials */}
          <div>
            {/* Newsletter */}
            <h3 className="text-sm font-semibold text-white mb-5 tracking-wider uppercase">
              Subscribe to Newsletter
            </h3>
            <form className="flex items-center gap-2 mb-8">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-2 text-sm bg-gray-900 text-gray-300 border border-gray-800 rounded-lg focus:outline-none focus:border-white placeholder-gray-500"
              />
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-white text-black font-semibold rounded-lg hover:bg-gray-200 transition-all duration-300"
              >
                Subscribe
              </button>
            </form>

            {/* Connect / Socials */}
            <h3 className="text-sm font-semibold text-white mb-5 tracking-wider uppercase">
              Connect with Us
            </h3>
            <div className="flex items-center gap-3">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-11 h-11 flex items-center justify-center rounded-full border border-gray-800 text-gray-400 hover:text-white hover:border-white transition-all duration-300 hover:scale-110"
                aria-label="GitHub"
              >
                <FaGithub className="text-lg" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-11 h-11 flex items-center justify-center rounded-full border border-gray-800 text-gray-400 hover:text-white hover:border-white transition-all duration-300 hover:scale-110"
                aria-label="Twitter"
              >
                <FaTwitter className="text-lg" />
              </a>
              <a
                href="https://discord.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-11 h-11 flex items-center justify-center rounded-full border border-gray-800 text-gray-400 hover:text-white hover:border-white transition-all duration-300 hover:scale-110"
                aria-label="Discord"
              >
                <FaDiscord className="text-lg" />
              </a>
              <a
                href="https://youtube.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-11 h-11 flex items-center justify-center rounded-full border border-gray-800 text-gray-400 hover:text-white hover:border-white transition-all duration-300 hover:scale-110"
                aria-label="YouTube"
              >
                <FaYoutube className="text-lg" />
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-16 pt-8 border-t border-gray-900">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-500">
            <p className="font-semibold">
              © {new Date().getFullYear()} Manhwa.ai - All rights reserved.
            </p>
            <p className="font-semibold">
              Designed & Developed with by{" "}
              <a
                href="https://github.com/SubhradeepNathGit"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 font-semibold hover:text-white transition-colors duration-300"
              >
                Subhradeep Nath
              </a>
              {" "}&{" "}
              <a
                href="https://github.com/anurag-bitan"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 font-semibold hover:text-white transition-colors duration-300"
              >
                Anurag Bhattacharya
              </a>
            </p>
          </div>
        </div>
      </div>


    </footer>
  );
};

export default Footer;