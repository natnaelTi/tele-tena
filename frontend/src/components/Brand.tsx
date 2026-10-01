import { Link } from "react-router-dom";
export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="brand" aria-label="TeleTena home">
      <img src={import.meta.env.BASE_URL + "brand/symbol.svg"} alt="" width="36" height="36" />
      {!compact && <span>TeleTena</span>}
    </Link>
  );
}
export function ConversationArt() {
  return (
    <svg
      className="conversation-art"
      viewBox="0 0 500 440"
      role="img"
      aria-label="Two conversation shapes making space for one another"
    >
      <ellipse cx="250" cy="396" rx="168" ry="16" fill="#D7E2DC" />
      <path
        d="M54 183C54 101 110 51 192 51h51c55 0 84 33 84 85v81c0 48-32 78-80 78h-73l-64 42 11-62c-45-13-67-45-67-92Z"
        fill="#126B64"
      />
      <path
        d="M253 172h55c84 0 139 48 139 113 0 42-22 72-58 88l9 43-49-29h-96c-49 0-78-30-78-80v-55c0-49 29-80 78-80Z"
        fill="#F2BC97"
      />
      <path
        d="M110 160c15-19 34-28 55-25m-60 57c26-3 43 6 58 20"
        fill="none"
        stroke="#CDE6DF"
        strokeWidth="9"
        strokeLinecap="round"
      />
      <path
        d="M299 261c15-11 33-11 49 0m-50 46c18 12 35 12 51 0"
        fill="none"
        stroke="#714C38"
        strokeWidth="9"
        strokeLinecap="round"
      />
      <path
        d="m359 70 13-25m18 46 28-8"
        stroke="#126B64"
        strokeWidth="6"
        strokeLinecap="round"
      />
      <circle cx="94" cy="363" r="9" fill="#74A89D" />
    </svg>
  );
}
