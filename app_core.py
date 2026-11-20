import re
def parse_tip(t):
 odds=re.search(r'(?:odds?\s*[:=@-]?\s*|@\s*)(\d+(?:\.\d+)?)',t,re.I)
 market=re.search(r'((?:over|under)\s*\d+(?:\.\d+)?(?:\s*(?:goals?|points?))?|(?:home|away)\s*(?:win|to score)|both teams to score)',t,re.I)
 return (market.group(1) if market else '',float(odds.group(1)) if odds else None)
