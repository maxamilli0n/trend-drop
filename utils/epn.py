from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import os
from dotenv import load_dotenv, find_dotenv

# Ensure root .env is loaded
load_dotenv(find_dotenv(usecwd=True), override=False)


def affiliate_wrap(url: str, custom_id: str = "trenddrop") -> str:
	"""
	Add EPN tracking params directly to the item URL to avoid rover 1x1.
	"""
	campid = os.environ.get("EPN_CAMPAIGN_ID")
	if not campid:
		return url

	u = urlparse(url)
	query = dict(parse_qsl(u.query))

	query.update({
		"mkcid": "1",
		"mkrid": "711-53200-19255-0",
		"mkevt": "1",
		"campid": campid,
		"customid": custom_id or "trenddrop",
		"toolid": "10001",
	})

	new_query = urlencode(query, doseq=True)
	return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
