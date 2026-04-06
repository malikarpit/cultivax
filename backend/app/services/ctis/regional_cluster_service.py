"""Regional cluster aggregation service for prospective yield updates."""

from math import sqrt

from sqlalchemy.orm import Session

from app.models.regional_cluster import RegionalCluster


class RegionalClusterService:
    def __init__(self, db: Session):
        self.db = db

    def update_from_yield(
        self,
        *,
        crop_type: str,
        region: str,
        season: str | None,
        delay_days: float,
        yield_value: float,
    ) -> RegionalCluster:
        cluster = (
            self.db.query(RegionalCluster)
            .filter(
                RegionalCluster.crop_type == crop_type,
                RegionalCluster.region == region,
                RegionalCluster.season == season,
                RegionalCluster.is_deleted == False,
            )
            .first()
        )

        if not cluster:
            cluster = RegionalCluster(
                crop_type=crop_type,
                region=region,
                season=season,
                sample_size=0,
                avg_delay=0.0,
                avg_yield=0.0,
            )
            self.db.add(cluster)
            self.db.flush()

        old_n = int(cluster.sample_size or 0)
        new_n = old_n + 1

        old_avg_delay = float(cluster.avg_delay or 0.0)
        old_avg_yield = float(cluster.avg_yield or 0.0)

        new_avg_delay = old_avg_delay + (float(delay_days) - old_avg_delay) / new_n
        new_avg_yield = old_avg_yield + (float(yield_value) - old_avg_yield) / new_n

        cluster.std_dev_delay = self._updated_std_dev(
            old_n=old_n,
            old_mean=old_avg_delay,
            old_std=cluster.std_dev_delay,
            x=float(delay_days),
            new_mean=new_avg_delay,
        )
        cluster.std_dev_yield = self._updated_std_dev(
            old_n=old_n,
            old_mean=old_avg_yield,
            old_std=cluster.std_dev_yield,
            x=float(yield_value),
            new_mean=new_avg_yield,
        )

        cluster.avg_delay = float(round(new_avg_delay, 4))
        cluster.avg_yield = float(round(new_avg_yield, 4))
        cluster.sample_size = new_n
        cluster.last_updated_from_count = new_n
        cluster.confidence_interval_95 = self._compute_ci95(cluster)

        return cluster

    def _updated_std_dev(
        self,
        *,
        old_n: int,
        old_mean: float,
        old_std: float | None,
        x: float,
        new_mean: float,
    ) -> float:
        if old_n <= 0:
            return 0.0

        m2_old = (float(old_std or 0.0) ** 2) * old_n
        m2_new = m2_old + (x - old_mean) * (x - new_mean)
        return float(round(sqrt(max(m2_new / (old_n + 1), 0.0)), 4))

    def _compute_ci95(self, cluster: RegionalCluster) -> dict:
        n = max(int(cluster.sample_size or 0), 1)
        z = 1.96

        std_delay = float(cluster.std_dev_delay or 0.0)
        std_yield = float(cluster.std_dev_yield or 0.0)

        delay_margin = z * (std_delay / sqrt(n)) if n > 1 else 0.0
        yield_margin = z * (std_yield / sqrt(n)) if n > 1 else 0.0

        return {
            "delay": {
                "lower": float(
                    round(float(cluster.avg_delay or 0.0) - delay_margin, 4)
                ),
                "upper": float(
                    round(float(cluster.avg_delay or 0.0) + delay_margin, 4)
                ),
            },
            "yield": {
                "lower": float(
                    round(float(cluster.avg_yield or 0.0) - yield_margin, 4)
                ),
                "upper": float(
                    round(float(cluster.avg_yield or 0.0) + yield_margin, 4)
                ),
            },
        }
