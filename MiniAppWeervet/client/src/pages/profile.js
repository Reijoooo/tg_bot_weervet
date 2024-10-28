import React from 'react';
import { useNavigate } from "react-router-dom";

const profile = () => {
    const navigate = useNavigate();
    navigate("/profile");
    return(
        <p>Профиль</p>
    );
}

export default profile;