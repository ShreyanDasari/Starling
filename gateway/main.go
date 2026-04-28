package main

import (
	"encoding/json"
	"log"
	"net/http"
)

// Message matches exactly what your React frontend sends
type Message struct {
	ID      string `json:"id"`
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	Messages []Message `json:"messages"`
}

type ChatResponse struct {
	Content string `json:"content"`
}

func main() {
	http.HandleFunc("/api/chat", handleChat)
	http.HandleFunc("/health",   handleHealth)

	log.Println("🐦 Gateway running on http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func handleChat(w http.ResponseWriter, r *http.Request) {
	// Allow requests from your Vite dev server
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Content-Type", "application/json")

	// Handle the preflight OPTIONS request browsers send first
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}

	// Parse the messages array from the frontend
	var req ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad JSON", http.StatusBadRequest)
		return
	}

	// Find the last thing the user said
	var lastMessage string
	for i := len(req.Messages) - 1; i >= 0; i-- {
		if req.Messages[i].Role == "user" {
			lastMessage = req.Messages[i].Content
			break
		}
	}

	log.Printf("📨 Received: %q", lastMessage)

	// Hardcoded reply for now — we'll replace this next
	reply := "Gateway received: \"" + lastMessage + "\". Agent coming soon."

	json.NewEncoder(w).Encode(ChatResponse{Content: reply})
}