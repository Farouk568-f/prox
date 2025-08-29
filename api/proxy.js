export default async function handler(req) {
  const { searchParams } = new URL(req.url);
  const url = searchParams.get("url");
  if (!url) {
    return new Response("Please provide ?url=", { status: 400 });
  }

  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": req.headers.get("user-agent") || "",
        "Referer": "https://fmoviesunblocked.net/",
        "Origin": "https://fmoviesunblocked.net/",
        "Accept-Encoding": "identity",
      },
    });

    const headers = new Headers(res.headers);
    headers.set("Access-Control-Allow-Origin", "*");
    headers.set("Access-Control-Expose-Headers", "*");

    return new Response(res.body, {
      status: res.status,
      headers,
    });
  } catch (err) {
    return new Response("Upstream error: " + err.message, { status: 502 });
  }
}
