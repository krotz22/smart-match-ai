require('dotenv').config(); // must be at the top

const express = require("express");
const mongoose = require("mongoose");
const path = require("path");
 

const app = express();
app.use(cors({ origin: "*" })); 
app.use(express.json());
app.use(cors({ origin: "*" })); // or your frontend domain

app.use("/uploads", express.static(path.join(__dirname, "uploads")));

const resumeRoutes = require("./routes/resumeRoutes");
const jobRoutes = require("./routes/jobRoutes");
const shortlistRoutes = require("./routes/shortlistRoutes");

app.use("/api/resumes", resumeRoutes);
app.use("/api/jobs", jobRoutes);
app.use("/api/shortlists", shortlistRoutes);


const uri = process.env.MONGO_URL;

mongoose.connect(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log("✅ Connected to MongoDB Atlas using Mongoose"))
.catch(err => console.error("❌ MongoDB connection error:", err));

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
