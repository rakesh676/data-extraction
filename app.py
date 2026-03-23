import os
import json
import queue
import threading
from flask import Flask, request, jsonify, render_template, send_file, Response, stream_with_context
from scraper import GoogleMapsScraper
from utils import logger, save_to_excel

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stream')
def stream():
    categories_str = request.args.get('categories', '')
    categories = [c.strip() for c in categories_str.split(',') if c.strip()]
    location = request.args.get('location', '')
    max_results = int(request.args.get('max_results', 20))

    if not categories or not location:
        def error_gen():
            yield f"event: error\ndata: {json.dumps({'error': 'Categories and location are required.'})}\n\n"
        return Response(stream_with_context(error_gen()), mimetype='text/event-stream')

    logger.info(f"Streaming Scrape Request: {categories} in {location} (Max {max_results})")

    def generate():
        q = queue.Queue()
        
        def callback(data):
            q.put(("data", data))
            
        def run_scraper():
            try:
                scraper = GoogleMapsScraper(headless=True)
                leads = scraper.scrape(
                    categories=categories,
                    location=location,
                    max_results_per_category=max_results,
                    yield_callback=callback
                )
                
                if leads:
                    filename = "leads.xlsx"
                    save_to_excel(leads, filename=filename)
                    q.put(("done", {"count": len(leads), "download_url": "/api/download"}))
                else:
                    q.put(("error", "No data found."))
            except Exception as e:
                logger.error(f"Scraping error: {e}")
                q.put(("error", str(e)))
                
        # Start scraping in background thread
        threading.Thread(target=run_scraper, daemon=True).start()
        
        while True:
            msg_type, payload = q.get()
            if msg_type == "data":
                yield f"event: data\ndata: {json.dumps(payload)}\n\n"
            elif msg_type == "done":
                yield f"event: done\ndata: {json.dumps(payload)}\n\n"
                break
            elif msg_type == "error":
                yield f"event: error\ndata: {json.dumps({'error': payload})}\n\n"
                break

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/download', methods=['GET'])
def download():
    file_path = os.path.join(os.getcwd(), 'leads.xlsx')
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found.", 404

if __name__ == '__main__':
    # Ensure static and templates folders exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    # Turn off reloader inside terminal loops or the process clones weirdly.
    app.run(debug=True, use_reloader=False, port=5000)
