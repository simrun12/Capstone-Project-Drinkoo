"""
Simple HTTP server to serve DRINKOO frontend files.

Run this from the project root:
    python -m http.server 3000 --directory frontend

Or from the frontend folder:
    python -m http.server 3000

Then visit: http://localhost:3000
"""

if __name__ == "__main__":
    import http.server
    import socketserver
    import os

    # Change to frontend directory
    os.chdir("frontend")

    PORT = 3000
    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"✓ DRINKOO Frontend Server Started")
        print(f"  Server: http://localhost:{PORT}")
        print(f"  Login: http://localhost:{PORT}")
        print(f"  Dashboard: http://localhost:{PORT}/dashboard.html")
        print(f"\nPress Ctrl+C to stop the server")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Server stopped")
