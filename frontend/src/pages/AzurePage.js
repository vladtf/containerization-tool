import { Container } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import { ToastContainer } from "react-toastify";
import CustomFooter from "../components/CustomFooter";

const AzurePage = () => {
  return (
    <Container>
      <CustomNavbar />
      <ToastContainer />


      

      <CustomFooter />
    </Container>
  );
};

export default AzurePage;
