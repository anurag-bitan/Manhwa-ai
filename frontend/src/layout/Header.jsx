// src/components/layout/Navbar.jsx
import React, { useState, useEffect, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, Video, Home, Mail } from "lucide-react";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Lock scroll when menu is open (prevent background scrolling)
  useEffect(() => {
    if (isOpen) {
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.overflow = "hidden";
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    } else {
      document.body.style.overflow = "unset";
      document.body.style.paddingRight = "0px";
    }
    
    return () => {
      document.body.style.overflow = "unset";
      document.body.style.paddingRight = "0px";
    };
  }, [isOpen]);

  // Close menu on ESC key and handle window resize
  const handleKeyDown = useCallback((e) => {
    if (e.key === "Escape" && isOpen) {
      setIsOpen(false);
    }
  }, [isOpen]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    
    // Close mobile menu on window resize to desktop
    const handleResize = () => {
      if (window.innerWidth >= 768 && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("resize", handleResize);
    };
  }, [handleKeyDown, isOpen]);

  // Nav links
  const navLinks = [
    { name: "Home", path: "/", icon: Home },
    // { name: "About", path: "/about", icon: Video },
    { name: "Upload", path: "/home", icon: Video },
    
    { name: "Contact", path: "/contact", icon: Mail },
  ];

  // Active route detection (fixed for home route)
  const isActive = (path) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  const handleNavigation = (path) => {
    setIsOpen(false);
    navigate(path);
  };

  return (
    <>
      {/* Navbar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-black/70 bg-opacity-80 backdrop-blur-lg shadow-lg"
            : "bg-black"
        }`}
      >
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 sm:h-20">
            {/* Logo - Responsive sizing */}
            <Link
              to="/"
              className="flex items-center gap-1.5 sm:gap-2 text-white font-bold text-lg sm:text-xl tracking-tight hover:opacity-80 transition-opacity duration-200 flex-shrink-0"
            >
              <svg 
                width="32" 
                height="32" 
                viewBox="0 0 32 32" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
                className="w-7 h-7 sm:w-8 sm:h-8 flex-shrink-0"
              >
               
                <circle cx="16" cy="16" r="14" stroke="white" strokeWidth="2" />
                <path d="M13 10L22 16L13 22V10Z" stroke="white" strokeWidth="2" strokeLinejoin="round" fill="none" />
              </svg>
              <span className="hidden xs:inline sm:inline">Manhwa.ai</span>
              <span className="xs:hidden sm:hidden">Manhwa</span>
            </Link>

            {/* Desktop Nav Links */}
            <div className="hidden md:flex items-center space-x-6 lg:space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className="relative text-gray-300 hover:text-white font-medium transition-colors duration-200 group text-sm lg:text-base"
                >
                  {link.name}
                  <span
                    className={`absolute left-0 -bottom-1 h-0.5 bg-purple-600 transition-all duration-300 ${
                      isActive(link.path) ? "w-full" : "w-0 group-hover:w-full"
                    }`}
                  />
                </Link>
              ))}
            </div>

            {/* CTA Button - Desktop */}
            <div className="hidden md:block">
              <button
                onClick={() => navigate("/home")}
                className="px-4 lg:px-5 py-2 bg-gradient-to-r from-pink-500 to-purple-600 hover:bg-blue-700 text-white font-semibold rounded-full transition-all duration-200 active:scale-95 text-sm lg:text-base whitespace-nowrap"
              >
                Create Video
              </button>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              aria-label={isOpen ? "Close menu" : "Open menu"}
              aria-expanded={isOpen}
              className="md:hidden p-2 text-white hover:bg-white/10 rounded-lg transition-colors duration-200 flex-shrink-0"
            >
              {isOpen ? <X className="w-5 h-5 sm:w-6 sm:h-6" /> : <Menu className="w-5 h-5 sm:w-6 sm:h-6" />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu Overlay & Sidebar */}
      {isOpen && (
        <>
          {/* Overlay - Full screen backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
            style={{ touchAction: 'none' }}
          />

          {/* Sliding Menu - Responsive width */}
          <aside
            className="fixed top-0 right-0 bottom-0 w-full xs:w-80 sm:w-72 bg-gray-900 z-50 p-4 sm:p-6 flex flex-col shadow-2xl md:hidden"
            style={{ maxWidth: '100vw' }}
          >
            {/* Header with Close Button */}
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
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
                <span className="text-white font-bold text-lg">Manhwa.ai</span>
              </div>
              
              <button
                onClick={() => setIsOpen(false)}
                aria-label="Close menu"
                className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Nav Links - Scrollable if needed */}
            <nav className="flex flex-col space-y-2 flex-1 overflow-y-auto">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 text-base sm:text-lg font-medium rounded-lg transition-colors duration-200 ${
                    isActive(link.path)
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:text-white hover:bg-white/5"
                  }`}
                >
                  <link.icon className="w-5 h-5 flex-shrink-0" />
                  <span>{link.name}</span>
                </Link>
              ))}
            </nav>

            {/* Mobile CTA - Sticky at bottom */}
            <div className="mt-auto pt-4 border-t border-gray-800">
              <button
                onClick={() => handleNavigation("/home")}
                className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all duration-200 active:scale-95 text-base"
              >
                Create Video
              </button>
            </div>
          </aside>
        </>
      )}

      {/* Spacer to prevent content from hiding under navbar */}
      <div className="h-16 sm:h-20" aria-hidden="true" />
    </>
  );
};

export default Navbar;