
// Admin Dashboard in pure JS using fetch and Tailwind (simplified)

const root = document.getElementById("root");

fetch("/admin/login_logs")
  .then((res) => res.json())
  .then((data) => {
    const logs = data.logs || [];
    root.innerHTML = `
      <h1 class="text-2xl font-bold mb-4">📊 Admin Login Dashboard</h1>
      <input id="search" placeholder="Filter by User ID..." class="mb-4 p-2 border rounded w-full" />
      <div class="overflow-x-auto">
        <table class="min-w-full bg-white shadow-md rounded">
          <thead><tr>
            <th class="px-4 py-2 text-left">User ID</th>
            <th class="px-4 py-2 text-left">Password</th>
            <th class="px-4 py-2 text-left">Result</th>
            <th class="px-4 py-2 text-left">Confidence</th>
            <th class="px-4 py-2 text-left">Similarity</th>
            <th class="px-4 py-2 text-left">Time</th>
          </tr></thead>
          <tbody id="log-body">
            ${logs.map(log => `
              <tr class="border-t">
                <td class="px-4 py-2">${log.user_id}</td>
                <td class="px-4 py-2">${log.password}</td>
                <td class="px-4 py-2">${log.result ? "✅" : "❌"}</td>
                <td class="px-4 py-2">${(log.confidence * 100).toFixed(1)}%</td>
                <td class="px-4 py-2">
                  <div class="w-full bg-gray-200 rounded">
                    <div class="bg-green-500 text-xs leading-none py-1 text-center text-white" style="width:${Math.round(log.similarity * 100)}%">
                      ${Math.round(log.similarity * 100)}%
                    </div>
                  </div>
                </td>
                <td class="px-4 py-2">${new Date(log.timestamp).toLocaleString()}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    document.getElementById("search").addEventListener("input", function () {
      const value = this.value.toLowerCase();
      const rows = document.querySelectorAll("#log-body tr");
      rows.forEach(row => {
        const user = row.children[0].textContent.toLowerCase();
        row.style.display = user.includes(value) ? "" : "none";
      });
    });
  });
