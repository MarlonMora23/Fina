import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
	sys.path.insert(0, str(BACKEND_DIR))

from agents.parser_agent import parserAgent

result = parserAgent("Compré 3 camisetas a 20 mil")

print(result)