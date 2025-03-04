'use client'
import axios from "axios";
import * as React from 'react';
import { useEffect, useRef, useState } from "react";
import { Box, Typography, TextField, Button, CssBaseline } from "@mui/material";
import ReactMarkdown from 'react-markdown';
import CircularProgress from '@mui/material/CircularProgress';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';


const ChatComponent = () => {
  const [messages, setMessages] = useState([
    { type: "bot", message: "Hello! How can I help you?" }
  ]);
  const [currMessage, setCurrMessage] = useState("");
  const [isFetching, setIsFetching] = useState(false);
  const [ragType, setRagType] = useState('');
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleRadioChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRagType((event.target as HTMLInputElement).value);
    console.log((event.target as HTMLInputElement).value)
  };


  // Handle sending a message
  const handleSend = async () => {
    if (!currMessage.trim()) return; // Prevent sending empty messages

    const userMessage = { type: "user", message: currMessage };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);
    setCurrMessage("");

    try {
      // Send request to backend
      setIsFetching(true)
      const response = await axios.post(`http://localhost:8000/api/${ragType}/answer-question`, {
        user_input: currMessage
      });
      setIsFetching(false)
      // Add bot's response to chat
      const botMessage = { type: "bot", message: response.data.data };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      setIsFetching(false)
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        { type: "bot", message: "Oops! Something went wrong." }
      ]);
    }
  };

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column'
      }}
    >
      <CssBaseline />
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "80vh",
          width: "50vw",
          border: 1,
          borderColor: "#fff",
          borderRadius: 5,
          overflowY: "auto",
          p: 2,
          scrollbarWidth: "none", // Firefox
          "&::-webkit-scrollbar": { display: "none" }, // Chrome, Safari, Edge
        }}
      >
        {/* Chat messages */}
        {messages.map((msg, i) => (
          <Box
            key={i}
            sx={{
              display: "inline-block",
              alignSelf: msg.type === "user" ? "flex-end" : "flex-start",
              bgcolor: msg.type === "user" ? "#7e64fc" : "#444444",
              color: "white",
              px: 2,
              py: 1,
              borderRadius: 2,
              maxWidth: "70%",
              wordWrap: "break-word",
              mt: 1,
            }}
          >
            {msg.type === "bot" ? (
              <ReactMarkdown>{msg.message}</ReactMarkdown>  // Render Markdown for bot messages
            ) : (
              <Typography sx={{ whiteSpace: "pre-wrap" }}>{msg.message}</Typography>
            )}
          </Box>
        ))}
        {isFetching &&
          <Box
            sx={{
              display: "inline-block",
              alignSelf: "flex-start",
              bgcolor: "#444444",
              px: 2,
              py: 1,
              borderRadius: 2,
              maxWidth: "70%",
              mt: 1,
            }}
          >
            <CircularProgress size="30px" />
          </Box>
        }

        <div ref={messagesEndRef} />



      </Box>
      <Box sx={{ display: "flex", p: 5, width: '50%' }}>
        <TextField
          fullWidth
          label="Type a message..."
          variant="outlined"
          value={currMessage}
          onChange={(e) => setCurrMessage(e.target.value)}
        />
        <Button onClick={handleSend} variant="contained" sx={{ ml: 1, bgcolor: '#7e64fc', color: '#fff' }}>
          Send
        </Button>
      </Box>
      <Box sx={{display:'flex',gap:10}}>
        <Button 
          variant="outlined" 
          sx={{ color: '#fff', borderColor: '#fff' }}
          onClick={()=>{setMessages([])}}
          >
          Clear Chat
        </Button>

        <FormControl>
          <RadioGroup
            row
            aria-labelledby="demo-radio-buttons-group-label"
            defaultValue="vector"
            name="radio-buttons-group"
            onChange={handleRadioChange}
          >
            <FormControlLabel value="vector" control={<Radio sx={{color:'#fff'}}/>} label="Vector" />
            <FormControlLabel value="kg" control={<Radio />} label="KG" />
            <FormControlLabel value="kg-vector" control={<Radio />} label="Vector + KG" />
          </RadioGroup>
        </FormControl>
      </Box>
    </Box>
  );
};

export default ChatComponent;
