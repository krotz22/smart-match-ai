import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from "./pages/header";
import Home from "./pages/home";
import JobsPage  from "./pages/jobs";
import UploadResumes from "./pages/resumes";
import SmartMatchPage from "./pages/match";

function App() {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/jobs" element={<JobsPage/>} />
        <Route path="/resumes" element={<UploadResumes/>}/>
        <Route path="/match" element={<SmartMatchPage/>}/>
        {/* <Route path="/jobs" element={<Jobs />} /> */}
      </Routes>
    </Router>
  );
}

export default App;
