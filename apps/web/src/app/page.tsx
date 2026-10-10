import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.content}>
        <h1>EduKit</h1>
        <p>Local-first digital transformation for schools.</p>
        <p>
          The application foundation is ready. School workflows have not yet
          been implemented.
        </p>
      </main>
    </div>
  );
}
