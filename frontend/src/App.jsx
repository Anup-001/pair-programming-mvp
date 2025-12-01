import React, { useState, useEffect, useRef, useCallback } from 'react';

// Configuration
const BASE_URL = 'http://127.0.0.1:8000';
const WS_URL = 'ws://127.0.0.1:8000/ws';

// Custom hook to handle debounce for AI Autocomplete
const useDebounce = (callback, delay) => {
    const timeoutRef = useRef(null);
    return useCallback((...args) => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
            callback(...args);
        }, delay);
    }, [callback, delay]);
};

// Main application component
const App = () => {
    // State initialization: The function inside useState runs only once on initial render.
    const [userId] = useState(() => Math.random().toString(36).substring(2, 8)); // <<< ADDED STABLE USER ID
    
    const [code, setCode] = useState("");
    const [roomId, setRoomId] = useState("");
    // We keep a stable ref to the WebSocket to avoid duplicate sockets
    // when React StrictMode mounts components twice in development.
    const wsRef = useRef(null);
    const connectingRef = useRef(false);
    const [isConnected, setIsConnected] = useState(false);
    const [message, setMessage] = useState("Click 'Create New Room' or enter a Room ID to start.");
    const [isLoading, setIsLoading] = useState(false);
    const [autocompleteSuggestion, setAutocompleteSuggestion] = useState("");

    const textareaRef = useRef(null);
    // Ref to track if the code change came from the network (to prevent echo/broadcast loops)
    const isNetworkUpdateRef = useRef(false);

    // --- WebSocket & Connection Logic ---

    const broadcastChange = useCallback((newCode) => {
        const socket = wsRef.current;
        if (socket && isConnected && socket.readyState === WebSocket.OPEN && !isNetworkUpdateRef.current) {
            socket.send(JSON.stringify({ type: "code_change", code: newCode }));
        }
    }, [isConnected]);
    // ... (rest of connectToRoom and useEffects remain the same)

    const connectToRoom = useCallback((id) => {
        if (!id) return;

        // If we're already connected or connecting, skip creating a new socket
        if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || connectingRef.current)) {
            console.log('Already connected or connecting — skipping new socket.');
            return;
        }

        setMessage("Connecting to room...");
        setIsLoading(true);
        connectingRef.current = true;

        const socket = new WebSocket(`${WS_URL}/${id}`);
        wsRef.current = socket;

        socket.onopen = () => {
            console.log("WebSocket connected.");
            connectingRef.current = false;
            setIsConnected(true);
            setRoomId(id);
            setMessage(`Connected to Room ID: ${id}. Start typing!`);
            setIsLoading(false);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "initial_state" || data.type === "code_update") {
                    isNetworkUpdateRef.current = true;
                    setCode(data.code);
                    setMessage(data.type === 'initial_state' ? `Connected to Room ID: ${id}. Initial code loaded from DB.` : `Connected to Room ID: ${id}. Live changes received.`);
                }
            } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
            }
        };

        socket.onclose = (event) => {
            console.log("WebSocket closed.", event.code, event.reason);
            connectingRef.current = false;
            setIsConnected(false);
            setIsLoading(false);
            if (event.code === 1008) {
                setMessage("Connection closed: Room does not exist. Please check the Room ID.");
            } else if (event.code !== 1000) {
                setMessage(`Connection closed with error. Code: ${event.code}.`);
            } else {
                setMessage("Disconnected successfully.");
            }
            // Clear ref
            if (wsRef.current === socket) wsRef.current = null;
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            connectingRef.current = false;
            setMessage("WebSocket Error. Check backend console and connectivity.");
            setIsConnected(false);
            setIsLoading(false);
        };
    }, []);

    // Cleanup and Network Flag Reset Effects
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                try { wsRef.current.close(); } catch (e) { }
                wsRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        // Reset the network flag shortly after code state updates via network
        if (isNetworkUpdateRef.current) {
            const timer = setTimeout(() => {
                isNetworkUpdateRef.current = false;
            }, 10); 
            return () => clearTimeout(timer);
        }
    }, [code]); 

    // Check URL path on initial load for existing room ID
    useEffect(() => {
        const path = window.location.pathname;
        const match = path.match(/\/room\/([a-zA-Z0-9]+)/);
        if (match && match[1]) {
            connectToRoom(match[1]);
        }
    }, [connectToRoom]);


    // --- AI Autocomplete Logic ---

    const fetchAutocomplete = async (currentCode, cursorPosition) => {
        if (!isConnected || currentCode.length < 5) {
             setAutocompleteSuggestion("");
             return;
        }

        try {
            const response = await fetch(`${BASE_URL}/autocomplete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: currentCode,
                    cursorPosition: cursorPosition,
                    language: "python"
                }),
            });

            if (response.ok) {
                const data = await response.json();
                setAutocompleteSuggestion(data.suggestion);
            } else {
                setAutocompleteSuggestion("");
            }
        } catch (error) {
            console.error("Autocomplete API error:", error);
            setAutocompleteSuggestion("");
        }
    };

    const debouncedAutocomplete = useDebounce(fetchAutocomplete, 600);

    // Autocomplete suggestion insertion
    const handleAutocompleteInsert = (suggestion) => {
        const textarea = textareaRef.current;
        if (!textarea) return;

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        
        // Insert suggestion at cursor position
        const newCode = code.substring(0, start) + suggestion + code.substring(end);
        
        setCode(newCode);
        broadcastChange(newCode);
        setAutocompleteSuggestion("");
        
        // Move cursor to the end of the inserted suggestion
        setTimeout(() => {
            textarea.selectionStart = start + suggestion.length;
            textarea.selectionEnd = start + suggestion.length;
            textarea.focus();
        }, 0);
    };


    // --- Event Handlers ---

    const handleCodeChange = (event) => {
        const newCode = event.target.value;
        setAutocompleteSuggestion(""); // Clear suggestion on user typing
        setCode(newCode);
        broadcastChange(newCode);
        debouncedAutocomplete(newCode, event.target.selectionStart);
    };

    // Keyboard shortcut for insertion (Tab key)
    const handleKeyDown = (event) => {
        if (event.key === 'Tab' && autocompleteSuggestion) {
            event.preventDefault(); // Prevent default tab behavior
            handleAutocompleteInsert(autocompleteSuggestion);
        }
    };

    const handleCreateRoom = async () => {
        setIsLoading(true);
        setMessage("Creating new room...");
        try {
            const response = await fetch(`${BASE_URL}/rooms`, { method: 'POST' });
            if (response.ok) {
                const data = await response.json();
                connectToRoom(data.roomId);
                window.history.pushState({}, '', `/room/${data.roomId}`); 
            } else {
                setMessage("Failed to create room. Check backend status.");
                setIsLoading(false);
            }
        } catch (error) {
            setMessage("Network error during room creation. Is the FastAPI server running?");
            setIsLoading(false);
            console.error("API Error:", error);
        }
    };

    const handleJoinRoom = () => {
        const inputId = prompt("Enter Room ID:");
        if (inputId) {
            connectToRoom(inputId);
            window.history.pushState({}, '', `/room/${inputId}`);
        }
    };

    // --- Render Logic ---
    const connectionStatusClass = isConnected ? "bg-green-500" : "bg-red-500";
    const connectionStatusText = isConnected ? "Live" : "Disconnected";

    const suggestionElement = autocompleteSuggestion ? (
        <div className="suggestion-box p-2 rounded-t text-sm font-mono text-gray-200 bg-gray-800">
            <strong className="text-purple-300">🤖 AI Suggestion:</strong>
            <span className="ml-2 text-purple-100">{autocompleteSuggestion}</span>
            <span className="ml-3 text-xs text-gray-400">Press Tab to accept</span>
        </div>
    ) : null;

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col p-4 font-inter">
            <header className="mb-4">
                <h1 className="text-3xl font-extrabold text-gray-800 tracking-tight">
                    CodeSync MVP 
                    <span className="text-base font-medium text-purple-600 ml-2">
                        (FastAPI/Postgres Real-Time Editor)
                    </span>
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                    Room ID: <span className="font-mono font-semibold text-gray-700">{roomId || "N/A"}</span> | 
                    User ID: <span className="font-mono font-semibold text-gray-700">{userId}</span> {/* <<< USED STABLE USER ID */}
                </p>
            </header>

            <div className="flex space-x-4 mb-4 items-center">
                <button 
                    onClick={handleCreateRoom}
                    disabled={isLoading || isConnected}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg shadow-md hover:bg-purple-700 transition disabled:bg-gray-400 font-medium"
                >
                    {isLoading && !isConnected ? 'Creating...' : 'Create New Room'}
                </button>
                <button 
                    onClick={handleJoinRoom}
                    disabled={isLoading || isConnected}
                    className="px-4 py-2 border border-purple-600 text-purple-600 rounded-lg shadow-md hover:bg-purple-50 transition disabled:border-gray-400 disabled:text-gray-400 font-medium"
                >
                    Join Room
                </button>

                <div className="flex items-center space-x-2 ml-auto p-2 rounded-full border border-gray-200 bg-white shadow-sm">
                    <span className={`w-3 h-3 ${connectionStatusClass} rounded-full animate-pulse`}></span>
                    <span className="text-sm font-medium text-gray-700">{connectionStatusText}</span>
                </div>
            </div>

            <div className={`p-3 text-sm rounded-lg shadow-inner ${isConnected ? 'bg-indigo-50 border-indigo-200' : 'bg-red-50 border-red-200'} border transition-colors duration-300`}>
                <p className="text-gray-700 font-medium">{message}</p>
                {autocompleteSuggestion && (
                    <p className="text-xs text-purple-600 mt-1 font-semibold">
                        🤖 AI Suggestion: Press <kbd className="px-1 bg-purple-200 rounded text-purple-800 shadow-sm">Tab</kbd> to accept.
                    </p>
                )}
            </div>
            
            <div className="relative flex-grow mt-4">
                <div className="editor-container">
                    {suggestionElement}
                    <textarea
                        ref={textareaRef}
                        value={code}
                        onChange={handleCodeChange}
                        onKeyDown={handleKeyDown}
                        disabled={!isConnected}
                        placeholder={isConnected ? "Start typing code (e.g., 'def' or 'class')..." : "Connect to a room to enable editing."}
                        className="editor w-full h-full min-h-[500px] rounded-b shadow-xl p-4 font-mono text-sm resize-none focus:ring-4 transition leading-relaxed"
                    />
                </div>
            </div>

            <footer className="mt-4 text-center text-xs text-gray-500">
                Ensure your FastAPI backend is running on {BASE_URL} and connected to PostgreSQL.
            </footer>
        </div>
    );
};

export default App;