import { Container } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import { ToastContainer } from "react-toastify";
import CustomFooter from "../components/CustomFooter";
import UploadFile from "../components/containers/UploadFile";
import ContainersData from "../components/containers/ContainersData";

const ContainersPage = () => {
  return (
    <Container>
      <CustomNavbar />
      <ToastContainer />
      <UploadFile />
      <ContainersData />
      <CustomFooter />
    </Container>
  );
};

export default ContainersPage;
