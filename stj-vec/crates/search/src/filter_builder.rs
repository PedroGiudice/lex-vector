use qdrant_client::qdrant::{Condition, Filter};

use crate::types::SearchFilters;

/// Constroi filtro Qdrant a partir dos campos suportados em `SearchFilters`.
///
/// Campos delegados ao Qdrant (payload indexes): `classe`, `tipo`, `secao`.
/// Retorna `None` se nenhum campo filtravel no Qdrant estiver preenchido.
pub fn build_qdrant_filter(filters: &SearchFilters) -> Option<Filter> {
    let mut conditions = Vec::new();

    if let Some(ref classe) = filters.classe {
        conditions.push(Condition::matches("classe", classe.clone()));
    }
    if let Some(ref tipo) = filters.tipo {
        conditions.push(Condition::matches("tipo", tipo.clone()));
    }
    if let Some(ref secao) = filters.secao {
        conditions.push(Condition::matches("secao", secao.clone()));
    }

    if conditions.is_empty() {
        None
    } else {
        Some(Filter::must(conditions))
    }
}

/// Retorna `true` se ha filtros residuais que precisam ser aplicados no SQLite.
///
/// Filtros residuais sao aqueles nao suportados no Qdrant payload
/// (ministro, datas, orgao_julgador, processo).
pub fn has_residual_filters(filters: &SearchFilters) -> bool {
    filters.ministro.is_some()
        || filters.data_from.is_some()
        || filters.data_to.is_some()
        || filters.orgao_julgador.is_some()
        || filters.processo_like.is_some()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_single_field_classe() {
        let filters = SearchFilters {
            classe: Some("REsp".to_string()),
            ..Default::default()
        };
        let filter = build_qdrant_filter(&filters);
        assert!(filter.is_some());
        let f = filter.unwrap();
        assert_eq!(f.must.len(), 1);
    }

    #[test]
    fn test_multiple_fields() {
        let filters = SearchFilters {
            classe: Some("REsp".to_string()),
            tipo: Some("acordao".to_string()),
            secao: Some("PRIMEIRA SECAO".to_string()),
            ..Default::default()
        };
        let filter = build_qdrant_filter(&filters);
        assert!(filter.is_some());
        let f = filter.unwrap();
        assert_eq!(f.must.len(), 3);
    }

    #[test]
    fn test_empty_returns_none() {
        let filters = SearchFilters::default();
        let filter = build_qdrant_filter(&filters);
        assert!(filter.is_none());
    }

    #[test]
    fn test_only_residual_fields_returns_none() {
        let filters = SearchFilters {
            ministro: Some("NANCY ANDRIGHI".to_string()),
            data_from: Some("2020-01-01".to_string()),
            ..Default::default()
        };
        let filter = build_qdrant_filter(&filters);
        assert!(filter.is_none());
    }

    #[test]
    fn test_has_residual_filters_true() {
        let filters = SearchFilters {
            ministro: Some("NANCY ANDRIGHI".to_string()),
            ..Default::default()
        };
        assert!(has_residual_filters(&filters));
    }

    #[test]
    fn test_has_residual_filters_false() {
        let filters = SearchFilters {
            classe: Some("REsp".to_string()),
            tipo: Some("acordao".to_string()),
            ..Default::default()
        };
        assert!(!has_residual_filters(&filters));
    }

    #[test]
    fn test_has_residual_with_data_range() {
        let filters = SearchFilters {
            data_from: Some("2020-01-01".to_string()),
            data_to: Some("2023-12-31".to_string()),
            ..Default::default()
        };
        assert!(has_residual_filters(&filters));
    }

    #[test]
    fn test_has_residual_with_processo_like() {
        let filters = SearchFilters {
            processo_like: Some("REsp%".to_string()),
            ..Default::default()
        };
        assert!(has_residual_filters(&filters));
    }
}
