import '../css/home.css';

function Home() {
  return (
    <div className="w-screen">
      {/* Hero Section */}
      <section className="bg-green-600 h-screen flex items-center justify-center">
        <h1 className="text-white text-7xl font-bold animate-bounce">Welcome to AI Recruiter</h1>
      </section>

      <section className="bg-red-600 py-20 px-8 max-w-screen-4xl mx-auto grid grid-cols-3 gap-8 items-center">
  
  <div className="col-span-2">
    <h2 className="text-white text-4xl font-semibold mb-4">About</h2>
    <p className="text-white text-lg max-w-2xl">
      This platform uses AI to streamline the hiring process, helping recruiters quickly find the best candidates.
    </p>
  </div>

  <div className="flex justify-end">
    <img
      src="https://i0.wp.com/cezannehr.com/wp-content/uploads/2023/11/What-are-the-most-important-qualities-of-a-great-HR-professional.png?fit=5200%2C2925&ssl=1"
      alt="HR Professional"
      className="w-[800px] h-[600] object-cover rounded shadow-lg"
    />
  </div>

</section>


      <section className="section">
      <h2 className="text-3xl font-bold text-center mb-8">Features</h2>

      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 ">
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <h3 className="text-xl font-semibold mb-2">Resume Upload</h3>
          <p className="text-gray-600">Easily upload and store candidate resumes securely.</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow text-center">
          <h3 className="text-xl font-semibold mb-2">AI Shortlisting</h3>
          <p className="text-gray-600">Automatically filter candidates based on job requirements.</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow text-center">
          <h3 className="text-xl font-semibold mb-2">Track Applications</h3>
          <p className="text-gray-600">View, manage, and track applications over time by year.</p>
        </div>
      </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 py-6 text-center">
        <p className="text-gray-400">&copy; 2025 AI Recruiter. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Home;
