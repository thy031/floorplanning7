/**
 * Site integration keys for EDA Algorithms Platform.
 * Course media: localhost → course-media/; deployed → jsDelivr monorepo paths.
 */
window.SITE_CONFIG = {
  brand: "EDA Algorithms Platform",
  ga4MeasurementId: "",
  feedbackIssuesUrl: "",
  simulatorUrl: "",
  /** GitHub org that hosts the monorepo (and thus CDN media). */
  githubOrg: "SJTU-YONGFU-RESEARCH-GRP",
  /** Monorepo name on GitHub (not per-course repos). */
  mediaRepo: "eda-learning",
  /**
   * Path under the monorepo before <courseId>/<moduleDir>/<file>.
   * Example CDN:
   *   …/eda-learning@main/courses/learn_partitioning/module02-01-kl-partition/slides.pdf
   */
  mediaPathPrefix: "courses",
  mediaBranch: "main",
  mediaCdn: "jsdelivr",
  /**
   * "auto" — localhost / GitHub Pages use this repo's course-media/; else CDN
   * "local" — always course-media next to the site (this standalone lab)
   * "cdn" — always jsDelivr/raw (eda-learning monorepo)
   */
  mediaSource: "local",
  progressKey: "eda.progress.v1",
};
