import React from "react";
import ReactDOM from "react-dom";

 class Back_button extends React.Component {
    onclick () {
      window.location.assign('http://localhost:3000/');
    }

    render() {
      return (<button class="back_button" onClick={(e) => this.onclick(e)}></button>);
    }
  }
export default Back_button;