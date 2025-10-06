import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const FAL_KEY = process.env.FAL_KEY;
    
    if (!FAL_KEY) {
      return NextResponse.json(
        { error: 'FAL_KEY not configured' },
        { status: 500 }
      );
    }

    const body = await request.json();
    const targetUrl = request.headers.get('X-Fal-Target-Url') || 'https://rest.alpha.fal.ai/tokens/';
    const method = request.headers.get('X-Fal-Method') || 'POST';

    console.log(`📡 Proxying ${method} request to: ${targetUrl}`);
    console.log(`📡 Request body:`, body);

    // Prepare fetch options
    const fetchOptions: RequestInit = {
      method,
      headers: {
        'Authorization': `Key ${FAL_KEY}`,
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(30000), // 30 second timeout
    };

    // Only add body for non-GET requests
    if (method !== 'GET') {
      fetchOptions.body = JSON.stringify(body);
    }

    // Forward the request to fal.ai with authentication
    const response = await fetch(targetUrl, fetchOptions);

    console.log(`📡 Response status: ${response.status}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('FAL API error:', errorText);
      return NextResponse.json(
        { error: `FAL API error: ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log(`📡 Response data:`, data);
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Proxy error:', error);
    if (error.name === 'TimeoutError' || error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Request timeout - FAL API took too long to respond' },
        { status: 504 }
      );
    }
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

