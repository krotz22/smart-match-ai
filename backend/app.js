require('dotenv').config(); // must be at the top
const cors = require('cors');
const express = require("express");
const mongoose = require("mongoose");
const path = require("path");


const app = express();
app.use(cors({ origin: "*" }));

// Allow larger request bodies (resumes sent as base64 inside JSON)
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ limit: "10mb", extended: true }));
console.log("JSON body limit set to 10mb");

app.use("/uploads", express.static(path.join(__dirname, "uploads")));

const resumeRoutes = require("./routes/resumeRoutes");
const jobRoutes = require("./routes/jobRoutes");
const shortlistRoutes = require("./routes/shortlistRoutes");

app.use("/api/resumes", resumeRoutes);
app.use("/api/jobs", jobRoutes);
app.use("/api/shortlists", shortlistRoutes);


const uri = process.env.MONGO_URL;

// useNewUrlParser and useUnifiedTopology are no longer needed
mongoose.connect(uri)
.then(() => console.log("✅ Connected to MongoDB Atlas using Mongoose"))
.catch(err => console.error("❌ MongoDB connection error:", err));

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
