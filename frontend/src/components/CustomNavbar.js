import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Navbar, Nav } from "react-bootstrap";
import { IoHome, IoChatbox } from "react-icons/io5";

const CustomNavbar = () => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? "active" : "";
  };

  return (
    <Navbar
      bg="dark"
      variant="dark"
      expand="lg"
      style={{
        borderBottomLeftRadius: "10px",
        borderBottomRightRadius: "10px",
      }}
    >
      {/* <Navbar.Brand
        as={Link}
        to="/"
        style={{ fontWeight: "bold", paddingLeft: "10px" }}
      >
        Containerization Tool
      </Navbar.Brand> */}
      <Navbar.Toggle aria-controls="navbar-nav" />
      <Navbar.Collapse id="navbar-nav">
        <Nav className="ml-auto">
          <Nav.Link as={Link} to="/" className={isActive("/")}>
            <IoHome size={20} style={{ marginRight: "5px" }} />
            Home
          </Nav.Link>
          <Nav.Link as={Link} to="/messages" className={isActive("/messages")}>
            <IoChatbox size={20} style={{ marginRight: "5px" }} />
            Messages
          </Nav.Link>
          <Nav.Link as={Link} to="/forwarding-rules" className={isActive("/forwarding-rules")}>
            <IoChatbox size={20} style={{ marginRight: "5px" }} />
            Forwarding Rules
          </Nav.Link>
        </Nav>
      </Navbar.Collapse>
    </Navbar>
  );
};

export default CustomNavbar;
