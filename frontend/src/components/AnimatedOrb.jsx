import React from "react";
import { motion } from "framer-motion";

const AnimatedOrb = ({ className, animateProps, transitionProps }) => {
  return (
    <motion.div
      className={`absolute rounded-full blur-xl ${className}`}
      animate={animateProps}
      transition={transitionProps}
    />
  );
};

export default AnimatedOrb;
