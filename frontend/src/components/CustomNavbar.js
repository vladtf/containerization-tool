import React from "react";
import { Nav, Navbar } from "react-bootstrap";
import { FaCloud } from "react-icons/fa";
import {
  IoChatbox,
  IoCube,
  IoCubeOutline,
  IoHome,
  IoSettingsSharp,
} from "react-icons/io5";
import { Link, useLocation } from "react-router-dom";

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
          <Nav.Link
            as={Link}
            to="/forwarding-rules"
            className={isActive("/forwarding-rules")}
          >
            <IoSettingsSharp size={20} style={{ marginRight: "5px" }} />
            Forwarding Rules
          </Nav.Link>
          <Nav.Link
            as={Link}
            to="/containers"
            className={isActive("/containers")}
          >
            <IoCube size={20} style={{ marginRight: "5px" }} />
            Containers
          </Nav.Link>
          <Nav.Link
            as={Link}
            to="/azure"
            className={isActive("/azure")}
          >
            <FaCloud size={20} style={{ marginRight: "5px" }} />
            Azure
          </Nav.Link>
        </Nav>
      </Navbar.Collapse>
    </Navbar>
  );
};

export default CustomNavbar;
