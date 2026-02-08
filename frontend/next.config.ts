import type { NextConfig } from "next";
import { resolve } from "path";

// Turbopack이 PostCSS에 `from` 옵션을 전달하지 않아서
// @tailwindcss/node의 CSS resolver가 상위 디렉토리(fix_ver/)를 기준으로 잡는 문제 수정
if (!process.env.NODE_PATH) {
  process.env.NODE_PATH = resolve(process.cwd(), "node_modules");
}

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
};

export default nextConfig;
