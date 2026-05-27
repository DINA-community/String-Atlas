import json
import logging
import configparser
from flask import Flask, jsonify, request, abort
from matcher.token_matcher import TokenMatcher
from matcher.token_matcher_decision import TokenMatcherDecision
from matcher.initialise.match_strategy_factory import match_strategy_factory

app = Flask(__name__)

handler = logging.FileHandler('error.log')
handler.setLevel(logging.ERROR)
app.logger.addHandler(handler)

config_mapping_file = 'config/tests/config_data_mapping.json'
with open(config_mapping_file, 'r') as file:
    config_fields = json.load(file)

config = configparser.ConfigParser()
config.read('config/api.ini')
API_KEY = config['API']['API_KEY']
API_PORT = int(config['API']['API_PORT'])
API_HOST = config['API']['API_HOST']
REDIS_HOST = config['API']['REDIS_HOST']
REDIS_PORT = int(config['API']['REDIS_PORT'])


# Middleware für Authentifizierung
def authenticate():
    api_key = request.headers.get('X-API-KEY')
    if api_key != API_KEY:
        abort(401, description="Unauthorized: Invalid API key")


@app.route('/api/match_all_with_strategies', methods=['POST'])
def product_type_with_fallbacks():
    authenticate()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    text = data.get('text', None)
    config = data.get('config', {})
    match_strategies = data.get('match_strategies') or []
    matches = []

    if text is None or (isinstance(text, str) and text.strip() == ""):
        return jsonify({"error": "Invalid 'text' data"}), 400

    if len(match_strategies) == 0:
        strategies = match_strategy_factory.get_all_strategies()
    else:
        strategies = match_strategy_factory.get_strategies_by_names(match_strategies)

    token_matcher_decision = TokenMatcherDecision(match_strategies=strategies, config=config)

    token_matcher = TokenMatcher()
    match = token_matcher.match_all_with_fallbacks(token_matcher_decision=token_matcher_decision, text=text)

    if match is not None:
        matches.append(match)
    return jsonify({"matches": matches})

if __name__ == '__main__':
    # TODO SSL connection
    # TODO Thesis
    # app.run(ssl_context=('cert.pem', 'key.pem'), debug=True)
    # TODO über config
    app.run(host=API_HOST, port=API_PORT, debug=True)
