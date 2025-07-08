function NavBar() {
  return (
    <nav className="bg-gray-800 text-white p-4 flex items-center justify-between">
      <h1 className="text-2xl font-bold">AI Recruiter</h1>

      <div className="flex gap-20 text-lg">
        <a href="/" className="hover:text-gray-300">Home</a>
        <a href="/jobs" className="hover:text-gray-300">Jobs</a>
        <a href="/resumes" className="hover:text-gray-300">Resumes</a>
        <a href="/match" className="hover:text-gray-300">Candidates</a>
      </div>
    </nav>
  );
}

export default NavBar;
