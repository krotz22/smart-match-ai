const express = require("express");
const router = express.Router();
const Job = require("../models/Job");

// GET all jobs
router.get("/", async (req, res) => {
  const jobs = await Job.find().sort({ createdAt: -1 });
  res.json(jobs);
});

// POST a new job
router.post("/", async (req, res) => {
  const { title, description, jobCode } = req.body;
  try {
    const job = new Job({ title, description, jobCode });
    await job.save();
    res.json({ message: "Job added", job });
  } catch (err) {
    res.status(500).json({ error: "Failed to add job" });
  }
});

// DELETE a job by ID
router.delete("/:id", async (req, res) => {
  try {
    await Job.findByIdAndDelete(req.params.id);
    res.json({ message: "Job deleted" });
  } catch (err) {
    res.status(500).json({ error: "Delete failed" });
  }
});

module.exports = router;
