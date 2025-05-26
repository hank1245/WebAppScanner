import React from "react";

const FormSection = ({ title, description, children }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      <div className="card-body">{children}</div>
    </div>
  );
};

export default FormSection;
