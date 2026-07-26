import { NextResponse } from "next/server";

export const dynamic = "force-dynamic"; // never cache; read env on each request

export async function GET(){
    return NextResponse.json({
        config: { API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"},
    });
}