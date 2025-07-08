function ResumeTable() {
    
    return(
        <div className="p-4">
                  <h2 className="text-2xl font-bold mb-4">Uploaded Resumes</h2>
                  <table className="min-w-full bg-white border border-gray-300">
                    <thead className="bg-gray-800 text-white">
                    <tr>
                        <th className="py-2 px-4 border">Name</th>
                        <th className="py-2 px-4 border">Code</th>
                        <th className="py-2 px-4 border">File</th>
                    </tr>
                    
                    </thead>
                    
                  </table>

        </div>
    );
}
export default ResumeTable;