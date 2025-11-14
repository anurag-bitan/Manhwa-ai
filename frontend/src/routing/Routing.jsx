// src/routing/Routing.jsx
import React, { Suspense, lazy } from "react";
import { Routes, Route, useLocation } from "react-router-dom";

// Layout components
import Navbar from "../layout/Header";
import Footer from "../layout/Footer";
import ScrollToTop from "../components/ScrollonTop"; 

// Lazy load pages for better performance
const LandingPage = lazy(() => import("../pages/Landing"));
const HomePage = lazy(() => import("../pages/Home"));
const ContactPage = lazy(() => import("../pages/Contact"));
const NotFoundPage = lazy(() => import("../pages/NotFound"));

// Layout Wrapper
const Layout = ({ children }) => {
  const location = useLocation();

  // Routes where we HIDE Navbar + Footer
  const hideLayoutRoutes = ["/login", "/signup", "/404"];
  const hideLayout = hideLayoutRoutes.includes(location.pathname);

  return (
    <>
      {!hideLayout && <Navbar />}
      {children}
      {!hideLayout && <Footer />}
    </>
  );
};

const Routing = () => {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center items-center h-screen">
          <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      {/* 👇 This ensures scroll resets on every route */}
      <ScrollToTop />  

      <Routes>
        {/* Pages wrapped with Layout */}
        <Route path="/" element={<Layout><LandingPage /></Layout>} />
        <Route path="/home" element={<Layout><HomePage /></Layout>} />
        <Route path="/contact" element={<Layout><ContactPage /></Layout>} />

        {/* Pages without Layout (auth or error pages) */}
        <Route path="/404" element={<NotFoundPage />} />

        {/* Catch-all for unmatched routes */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
};

export default Routing;
