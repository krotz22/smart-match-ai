const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const dotenv = require("dotenv");
const path = require("path");

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

const resumeRoutes = require("./routes/resumeRoutes");
const jobRoutes = require("./routes/jobRoutes");
const shortlistRoutes = require("./routes/shortlistRoutes");

app.use("/api/resumes", resumeRoutes);
app.use("/api/jobs", jobRoutes);
app.use("/api/shortlists", shortlistRoutes);

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    console.log("✅ MongoDB connected");
    app.listen(4000, () => console.log("🚀 Server on http://localhost:4000"));
  })
  .catch((err) => console.error("❌ DB Error:", err));
