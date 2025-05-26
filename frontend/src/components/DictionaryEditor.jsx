import React, { useState, useEffect } from "react";
import { getDefaultDictionary } from "../api";
import styles from "../styles/DictionaryEditor.module.css";

const DictionaryEditor = ({ onChange }) => {
  const [dictionaryItems, setDictionaryItems] = useState([]);
  const [newItem, setNewItem] = useState("");
  const [useDefaultDict, setUseDefaultDict] = useState(true);
  const [showAll, setShowAll] = useState(false);

  // Load default dictionary when component mounts
  useEffect(() => {
    if (useDefaultDict) {
      setDictionaryItems(getDefaultDictionary());
    }
  }, [useDefaultDict]);

  // Add item
  const handleAddItem = () => {
    if (newItem.trim()) {
      // Check if path has / at the end
      const formattedItem = newItem.trim().endsWith("/")
        ? newItem.trim()
        : `${newItem.trim()}/`;

      if (!dictionaryItems.includes(formattedItem)) {
        const updatedItems = [...dictionaryItems, formattedItem];
        setDictionaryItems(updatedItems);

        // Notify parent component of changes
        const addOperation = {
          type: "add",
          paths: [formattedItem],
        };

        onChange({
          operations: [addOperation],
          useDefault: useDefaultDict,
        });

        setNewItem("");
      } else {
        alert("This item already exists in the list.");
      }
    }
  };

  // Remove item
  const handleRemoveItem = (item) => {
    const updatedItems = dictionaryItems.filter((i) => i !== item);
    setDictionaryItems(updatedItems);

    // Notify parent component of changes
    const removeOperation = {
      type: "remove",
      paths: [item],
    };

    onChange({
      operations: [removeOperation],
      useDefault: useDefaultDict,
    });
  };

  // Toggle default dictionary usage
  const handleDefaultToggle = () => {
    const newValue = !useDefaultDict;
    setUseDefaultDict(newValue);

    if (newValue) {
      // Switch to using default dictionary
      setDictionaryItems(getDefaultDictionary());
    } else {
      // Stop using default dictionary, use only custom list
      setDictionaryItems([]);
    }

    // Notify parent component of changes
    onChange({
      operations: [],
      useDefault: newValue,
    });
  };

  // Calculate number of items to display
  const visibleItems = showAll ? dictionaryItems : dictionaryItems.slice(0, 10);

  return (
    <div className={styles.dictionaryEditor}>
      <h3 className={styles.formLabel}>Dictionary Settings</h3>
      <p className={styles.formHint}>
        Manage the list of directory paths to scan.
      </p>

      <div className={styles.checkboxGroup}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={useDefaultDict}
            onChange={handleDefaultToggle}
            className={styles.formCheckbox}
          />
          <span>Use Default Dictionary (Recommended)</span>
        </label>
      </div>

      <div className={styles.dictionaryInputGroup}>
        <input
          type="text"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          placeholder="Directory path to add (e.g., admin/)"
          className={styles.formControl}
        />
        <button
          type="button"
          onClick={handleAddItem}
          className={`${styles.btn} ${styles.btnSecondary}`}
          disabled={!newItem.trim()}
        >
          Add
        </button>
      </div>

      <div className={styles.dictionaryList}>
        <p className={styles.formHint}>
          Current dictionary items: {dictionaryItems.length}
          {dictionaryItems.length > 10 && !showAll && (
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className={styles.btnLink}
            >
              Show All
            </button>
          )}
          {showAll && (
            <button
              type="button"
              onClick={() => setShowAll(false)}
              className={styles.btnLink}
            >
              Collapse
            </button>
          )}
        </p>

        <div className={styles.dictionaryItems}>
          {visibleItems.length > 0 ? (
            visibleItems.map((item, index) => (
              <div key={index} className={styles.dictionaryItem}>
                <span>{item}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveItem(item)}
                  className={styles.btnClose}
                  aria-label="Remove"
                >
                  ×
                </button>
              </div>
            ))
          ) : (
            <p className={styles.emptyMessage}>Dictionary items are empty.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default DictionaryEditor;
