import React from "react";
import styles from "../styles/FormSection.module.css";

const FormSection = ({ title, description, children }) => {
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      <div className={styles.cardBody}>{children}</div>
    </div>
  );
};

export default FormSection;
