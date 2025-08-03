require('dotenv').config(); // must be at the top

const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const path = require("path");
 

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


const uri = process.env.MONGO_URI;

mongoose.connect(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log("✅ Connected to MongoDB Atlas using Mongoose"))
.catch(err => console.error("❌ MongoDB connection error:", err));

