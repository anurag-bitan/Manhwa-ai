import React, { useState } from "react";
import { motion } from "framer-motion";

const faqData = [
  {
    q: "How do I convert my manga to a video?",
    a: "Simply upload your manga PDF, choose your preferred mode, and click Generate Video. Our AI engine automatically creates a smooth, dynamic video version of your manga.",
  },
  {
    q: "Which file formats are supported?",
    a: "We currently support PDF uploads for manga conversion. The generated output is provided in standard MP4 format for easy sharing and playback.",
  },
  {
    q: "Can I preview the video before downloading?",
    a: "Yes! Once the video is generated, you can instantly preview it on the same page and download it when you're satisfied with the result.",
  },
  {
    q: "Is there a file size limit for uploads?",
    a: "To ensure fast and stable performance, we recommend keeping your manga file under 50MB. Larger files may take longer to process depending on system load.",
  },
  {
    q: "Do I need to install any software?",
    a: "No installation is required. Mangio.ai runs entirely in your browser — just upload, generate, and download without any setup.",
  },
  
  {
    q: "Is my uploaded manga data safe?",
    a: "Absolutely. All files are processed securely and automatically deleted after conversion to protect your privacy and intellectual property.",
  },
  //  {
  //   q: "Is the service free to use?",
  //   a: "Manghwa.ai offers a free trial with limited conversions. For extended access and higher-quality video exports, you can upgrade to a premium plan.",
  // },
];


const developers = [
  {
    name: "Subhradeep Nath",
    role: "Frontend (React)",
    img: "/SubhroDp.png",
    linkedin: "https://www.linkedin.com/in/subhradeep-nath-dev",
    github: "https://github.com/SubhradeepNathGit",
  },
  {
    name: "Anurag Bhattacharya",
    role: "Backend (Python)",
    img: "/Anurag.jpeg",
    linkedin: "https://www.linkedin.com/in/anurag-bhattacharya-256b351a4/",
    github: "https://github.com/anurag-bitan",
  },
];

const Contact = () => {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);

  const validate = () => {
    const err = {};
    if (!form.name.trim()) err.name = "Name is required";
    if (!form.email.trim()) err.email = "Email is required";
    else if (!/^\S+@\S+$/i.test(form.email)) err.email = "Invalid email";
    if (!form.message.trim()) err.message = "Message is required";
    return err;
  };

  const handleSubmit = async () => {
    const err = validate();
    setErrors(err);
    if (Object.keys(err).length) return;

    setLoading(true);
    await new Promise(r => setTimeout(r, 1000));
    console.log(form);
    setLoading(false);
    setSuccess(true);
    setForm({ name: "", email: "", message: "" });
    setTimeout(() => setSuccess(false), 4000);
  };

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      
      {/* Content */}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px- py-20 lg:py-5">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8 lg:mb-10"
        >
          <h1 className="text-3xl sm:text-4xl lg:text-4xl font-bold text-white mb-3">
            Contact Us
          </h1>
          <p className="text-gray-400 text-base">Have doubts or suggestions? Contact us directly with your queries </p>
        </motion.div>

        {/* Form + FAQ Grid */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 mb-16">
          
          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-gray-700/50 h-[500px] flex flex-col"
          >
            
            
            <div className="space-y-4 flex-1 flex flex-col">
              <div>
                <input
                  type="text"
                  placeholder="Your Name"
                  value={form.name}
                  onChange={e => setForm({...form, name: e.target.value})}
                  className="w-full p-3 rounded-xl bg-white/5 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
                {errors.name && <p className="text-red-400 text-sm mt-1">{errors.name}</p>}
              </div>

              <div>
                <input
                  type="email"
                  placeholder="Your Email"
                  value={form.email}
                  onChange={e => setForm({...form, email: e.target.value})}
                  className="w-full p-3 rounded-xl bg-white/5 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
                {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
              </div>

              <div className="flex-1 flex flex-col">
                <textarea
                  placeholder="Your Message"
                  value={form.message}
                  onChange={e => setForm({...form, message: e.target.value})}
                  className="w-full  max-h-50 flex-1 p-3 rounded-xl bg-white/5 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-500 resize-none"
                />
                {errors.message && <p className="text-red-400 text-sm mt-1">{errors.message}</p>}
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full py-3 rounded-full bg-gradient-to-r from-pink-500 to-purple-600 font-semibold  active:scale-90 transition-transform disabled:opacity-50"
              >
                {loading ? "Sending..." : "Send Message"}
              </button>

              {success && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-3 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-center"
                >
                  ✓ Message sent successfully!
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* FAQ */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-3"
          >
            {/* <h2 className="text-2xl text-center font-semibold mb-6">Frequently Asked Questions</h2> */}
            {faqData.map((item, i) => (
              <div 
                key={i} 
                className="bg-white/5 backdrop-blur-xl rounded-xl border border-gray-700/50 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full p-5 text-left flex justify-between items-center hover:bg-white/5 transition-colors"
                >
                  <p className="font-semibold text-lg pr-4">{item.q}</p>
                  <motion.svg
                    animate={{ rotate: openFaq === i ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="w-5 h-5 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </motion.svg>
                </button>
                <motion.div
                  initial={false}
                  animate={{
                    height: openFaq === i ? "auto" : 0,
                    opacity: openFaq === i ? 1 : 0
                  }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <p className="text-gray-400 text-sm px-5 pb-5">{item.a}</p>
                </motion.div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Developers */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}

        >
          <h2 className="text-3xl font-bold text-center mb-2">Meet the Developers</h2>
          <p className="text-gray-400 text-center mb-15">Feel free to reach out for collaboration or contributions</p>
          <div className="grid sm:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {developers.map((dev, i) => (
              <div
                key={i}
                className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50 text-center"
              >
                <img
                  src={dev.img}
                  alt={dev.name}
                  className="w-24 h-24 mx-auto rounded-full mb-4 border-3 border-gray-700 object-cover"
                />
                <h3 className="text-xl font-bold mb-1">{dev.name}</h3>
                <p className="text-gray-400 mb-4">{dev.role}</p>
                <div className="flex justify-center gap-4">
                  <a
                    href={dev.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:scale-110 transition-transform"
                  >
                    <svg className="w-6 h-6 fill-current text-blue-400 hover:text-blue-300" viewBox="0 0 24 24">
                      <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                    </svg>
                  </a>
                  <a
                    href={dev.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:scale-110 transition-transform"
                  >
                    <svg className="w-6 h-6 fill-current text-gray-400 hover:text-gray-300" viewBox="0 0 24 24">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Contact;