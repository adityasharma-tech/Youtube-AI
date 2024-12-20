import os
from flask import Flask, request, jsonify 
from youtubeai import YoutubeChannelLm

app = Flask(__name__)
youtube_channelml = YoutubeChannelLm(channel_id="UCf9T51_FmMlfhiGpoes0yFA", api_key=os.getenv('YOUTUBE_API_KEY'))

@app.route('/submit', methods=['POST'])
def submit_data():
    # Retrieve JSON data from the request
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # Process the data (for example, print it or return it)
    query = data.get("query", "Anonymous")
    response = youtube_channelml.query(query)

    return jsonify({"message": response})

if __name__ == '__main__':
    app.run(debug=True, port=8088)

