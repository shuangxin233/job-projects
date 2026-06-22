export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  imageUrl?: string;
  timestamp: number;
  loading?: boolean;
  streaming?: boolean;
}

export interface ApiChatMessage {
  role: MessageRole;
  content: string;
  image_url?: string | null;
  created_at?: string;
}

export interface Recipe {
  title: string;
  score?: number;
  reason?: string;
  difficulty?: string;
  url?: string;
  steps?: string[];
  seasonings?: string[];
  cooking_time?: string;
}
