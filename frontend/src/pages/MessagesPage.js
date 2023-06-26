import React, { useState, useEffect } from "react";
import { Container } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";

const MessagesPage = () => {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get("http://localhost:8180/messages/all");
        setMessages(response.data);
      } catch (error) {
        console.log(error);
      }
    };

    fetchData();
  }, []);

  return (
    <Container>
      <CustomNavbar />
      <div>
        <h1>Messages Page</h1>
        <ul>
          {messages.map((message, index) => (
            <li key={index}>{message.message}</li>
          ))}
        </ul>
      </div>
    </Container>
  );
};

export default MessagesPage;
