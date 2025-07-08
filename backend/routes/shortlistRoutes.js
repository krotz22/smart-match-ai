// routes/shortlistRoutes.js
const express = require("express");
const router = express.Router();
const Shortlist = require("../models/Shortlist");

router.post("/", async (req, res) => {
  try {
    const newShortlist = new Shortlist(req.body);
    const saved = await newShortlist.save();
    res.status(201).json({ message: "Shortlist saved", data: saved });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// GET shortlisted candidates by jobCode



router.get("/", async (req, res) => {
  const { code } = req.query;

  try {
    const data = await Shortlist.find({ jobCode: code });
    res.json(data);
  } catch (err) {
    console.error("Error fetching shortlists:", err);
    res.status(500).json({ error: "Failed to fetch shortlist data" });
  }
});




module.exports = router;
