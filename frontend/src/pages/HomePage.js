import React from "react";
import { Button, Container } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import {
  IoChatbox,
  IoCube,
  IoCubeOutline,
  IoHome,
  IoSettings,
  IoUnlink,
} from "react-icons/io5";

const HomePage = () => {
  const navbarLinks = [
    { path: "/", label: "Home", icon: <IoHome size={40} /> },
    { path: "/messages", label: "Messages", icon: <IoChatbox size={40} /> },
    {
      path: "/forwarding-rules",
      label: "Forwarding Rules",
      icon: <IoSettings size={40} />,
    },
    {
      path: "/containers",
      label: "Containers",
      icon: <IoCube size={40} />,
    },
    {
      path: "/",
      label: "Upcoming...",
      icon: <IoUnlink size={40} />,
    },
    {
      path: "/",
      label: "Upcoming...",
      icon: <IoUnlink size={40} />,
    },
    {
      path: "/",
      label: "Upcoming...",
      icon: <IoUnlink size={40} />,
    },
    {
      path: "/",
      label: "Upcoming...",
      icon: <IoUnlink size={40} />,
    },
    {
      path: "/",
      label: "Upcoming...",
      icon: <IoUnlink size={40} />,
    },
  ];

  return (
    <Container>
      <CustomNavbar />
      <Container style={{ marginTop: "20px", width: "70%" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "0px",
            justifyItems: "center",
          }}
        >
          {navbarLinks.map((link, index) => (
            <Button
              key={index}
              style={{
                height: "250px",
                width: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "0px",
              }}
              variant="outline-primary"
              onClick={() => (window.location.href = link.path)}
            >
              <div>{link.icon}</div>
              <div>
                <span>{link.label}</span>
              </div>
            </Button>
          ))}
        </div>
      </Container>
    </Container>
  );
};

export default HomePage;
