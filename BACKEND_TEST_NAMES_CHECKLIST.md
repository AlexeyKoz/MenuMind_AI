# MenuMindAI Backend Tests - Complete Name List

> **Total Tests: ~450+**  
> Use this as your implementation checklist ✓

---

## 📁 1. USERS APP (`apps/users/tests/`)

### `test_models.py` - User & Profile Models

#### TestUserModel
- [ ] `test_create_user_with_email_and_password_succeeds`
- [ ] `test_create_user_without_email_fails`
- [ ] `test_create_user_with_duplicate_email_fails`
- [ ] `test_create_user_with_invalid_email_format_fails`
- [ ] `test_email_normalization_lowercases_domain`
- [ ] `test_email_normalization_preserves_case_in_local_part`
- [ ] `test_user_string_representation_returns_email`
- [ ] `test_user_has_default_timestamps`
- [ ] `test_user_email_verified_defaults_to_false`
- [ ] `test_user_is_active_defaults_to_true`
- [ ] `test_user_is_staff_defaults_to_false`
- [ ] `test_user_password_is_hashed_not_plain_text`
- [ ] `test_user_check_password_validates_correctly`

#### TestUserProfile
- [ ] `test_profile_created_automatically_with_user_via_signal`
- [ ] `test_profile_one_to_one_relationship_with_user`
- [ ] `test_profile_update_updates_modified_timestamp`
- [ ] `test_profile_preferences_json_field_accepts_valid_data`
- [ ] `test_profile_preferences_invalid_json_rejected`
- [ ] `test_profile_preferred_language_choices_validated`
- [ ] `test_profile_preferred_language_defaults_to_en`
- [ ] `test_profile_cascade_deletes_with_user`
- [ ] `test_profile_string_representation`

---

### `test_serializers.py` - User Serializers

#### TestUserRegistrationSerializer
- [ ] `test_valid_registration_data_serializes_correctly`
- [ ] `test_registration_creates_user_in_database`
- [ ] `test_registration_with_short_password_fails_validation`
- [ ] `test_registration_with_weak_password_fails_validation`
- [ ] `test_registration_with_invalid_email_fails_validation`
- [ ] `test_registration_with_duplicate_email_fails_validation`
- [ ] `test_registration_password_confirmation_mismatch_fails`
- [ ] `test_registration_password_not_included_in_serialized_output`
- [ ] `test_registration_user_created_with_hashed_password`
- [ ] `test_registration_profile_created_automatically`
- [ ] `test_registration_email_verified_set_to_false_by_default`
- [ ] `test_registration_validates_email_format`

#### TestUserLoginSerializer
- [ ] `test_valid_login_credentials_authenticate_successfully`
- [ ] `test_invalid_email_login_fails_with_error`
- [ ] `test_invalid_password_login_fails_with_error`
- [ ] `test_nonexistent_email_login_fails_with_error`
- [ ] `test_inactive_user_login_fails_with_error`
- [ ] `test_unverified_email_login_succeeds_with_warning_flag`
- [ ] `test_case_insensitive_email_login`
- [ ] `test_whitespace_trimmed_from_email`

#### TestUserProfileSerializer
- [ ] `test_profile_serialization_includes_all_fields`
- [ ] `test_profile_deserialization_updates_correctly`
- [ ] `test_profile_partial_update_allowed`
- [ ] `test_language_preference_update_validates_choices`
- [ ] `test_language_preference_invalid_choice_rejected`
- [ ] `test_nested_preferences_json_field_update`
- [ ] `test_readonly_fields_cannot_be_modified`
- [ ] `test_user_field_included_in_serialization`

#### TestUserDetailSerializer
- [ ] `test_user_detail_includes_profile_nested`
- [ ] `test_user_detail_includes_email_verified_status`
- [ ] `test_user_detail_excludes_sensitive_fields`
- [ ] `test_user_detail_includes_date_joined`

---

### `test_views.py` - User API Views

#### TestUserRegistrationView
- [ ] `test_registration_post_with_valid_data_returns_201`
- [ ] `test_registration_creates_user_in_database`
- [ ] `test_registration_creates_profile_automatically`
- [ ] `test_registration_sends_verification_email`
- [ ] `test_registration_returns_jwt_access_token`
- [ ] `test_registration_returns_jwt_refresh_token`
- [ ] `test_registration_with_invalid_data_returns_400`
- [ ] `test_registration_with_duplicate_email_returns_400`
- [ ] `test_registration_with_missing_fields_returns_400`
- [ ] `test_registration_rate_limiting_enforced_after_threshold`
- [ ] `test_registration_allows_anonymous_access`

#### TestUserLoginView
- [ ] `test_login_post_with_valid_credentials_returns_200`
- [ ] `test_login_returns_jwt_access_token`
- [ ] `test_login_returns_jwt_refresh_token`
- [ ] `test_login_with_invalid_credentials_returns_401`
- [ ] `test_login_with_invalid_email_returns_401`
- [ ] `test_login_with_invalid_password_returns_401`
- [ ] `test_login_with_inactive_user_returns_401`
- [ ] `test_login_updates_last_login_timestamp`
- [ ] `test_login_with_unverified_email_includes_warning_flag`
- [ ] `test_login_rate_limiting_prevents_brute_force`
- [ ] `test_login_allows_anonymous_access`

#### TestUserProfileView
- [ ] `test_get_profile_requires_authentication`
- [ ] `test_get_profile_returns_current_user_data`
- [ ] `test_get_profile_includes_nested_profile_data`
- [ ] `test_get_profile_unauthenticated_returns_401`
- [ ] `test_update_profile_with_valid_data_returns_200`
- [ ] `test_update_profile_changes_persisted_to_database`
- [ ] `test_update_profile_partial_update_allowed`
- [ ] `test_update_profile_requires_authentication`
- [ ] `test_update_profile_unauthenticated_returns_401`
- [ ] `test_update_profile_cannot_change_email`
- [ ] `test_update_profile_cannot_change_user_id`

#### TestTokenRefreshView
- [ ] `test_refresh_with_valid_refresh_token_returns_new_access_token`
- [ ] `test_refresh_with_invalid_token_returns_401`
- [ ] `test_refresh_with_expired_refresh_token_returns_401`
- [ ] `test_refresh_with_malformed_token_returns_401`
- [ ] `test_refresh_updates_access_token_only`
- [ ] `test_refresh_does_not_change_refresh_token`
- [ ] `test_refresh_allows_anonymous_access`

#### TestUserLogoutView
- [ ] `test_logout_blacklists_refresh_token`
- [ ] `test_logout_requires_authentication`
- [ ] `test_logout_returns_200_on_success`
- [ ] `test_logout_token_cannot_be_reused_after_logout`

---

### `test_permissions.py` - User Permissions

#### TestIsAuthenticated
- [ ] `test_authenticated_user_has_permission`
- [ ] `test_unauthenticated_user_denied_permission`
- [ ] `test_user_with_invalid_token_denied_permission`
- [ ] `test_user_with_expired_token_denied_permission`

#### TestIsVerifiedEmail
- [ ] `test_verified_email_user_has_permission`
- [ ] `test_unverified_email_user_denied_permission`
- [ ] `test_permission_message_descriptive`

#### TestIsOwnerOrAdmin
- [ ] `test_owner_has_permission`
- [ ] `test_admin_has_permission`
- [ ] `test_other_user_denied_permission`
- [ ] `test_unauthenticated_user_denied_permission`

---

### `test_auth_flows.py` - Complete Auth Flows

#### TestCompleteRegistrationFlow
- [ ] `test_registration_to_email_verification_to_login_complete_flow`
- [ ] `test_registration_creates_user_and_sends_verification_email`
- [ ] `test_unverified_user_cannot_access_protected_resources`
- [ ] `test_email_verification_enables_access_to_protected_resources`
- [ ] `test_verification_link_contains_valid_token`
- [ ] `test_verification_link_expires_after_24_hours`
- [ ] `test_verification_link_single_use_only`
- [ ] `test_verification_link_invalid_token_fails`

#### TestPasswordResetFlow
- [ ] `test_password_reset_request_sends_email`
- [ ] `test_password_reset_email_contains_valid_token`
- [ ] `test_password_reset_with_valid_token_updates_password`
- [ ] `test_password_reset_token_expires_after_time_limit`
- [ ] `test_password_reset_token_single_use_only`
- [ ] `test_old_password_invalid_after_reset`
- [ ] `test_new_password_allows_successful_login`
- [ ] `test_password_reset_with_invalid_token_fails`
- [ ] `test_password_reset_for_nonexistent_email_fails_silently`

#### TestTokenRefreshFlow
- [ ] `test_access_token_expires_and_refresh_provides_new_one`
- [ ] `test_expired_access_token_rejected`
- [ ] `test_refresh_token_provides_valid_new_access_token`
- [ ] `test_new_access_token_allows_api_access`

---

### `test_google_oauth.py` - Google OAuth Integration

#### TestGoogleOAuthAuthentication
- [ ] `test_google_oauth_with_valid_authorization_code_creates_user`
- [ ] `test_google_oauth_with_valid_code_returns_jwt_tokens`
- [ ] `test_google_oauth_with_existing_user_returns_tokens_without_creating_duplicate`
- [ ] `test_google_oauth_automatically_verifies_email`
- [ ] `test_google_oauth_with_invalid_code_returns_400`
- [ ] `test_google_oauth_with_expired_code_returns_400`
- [ ] `test_google_oauth_with_id_token_authenticates_successfully`
- [ ] `test_google_oauth_with_invalid_id_token_returns_400`
- [ ] `test_google_oauth_handles_google_api_errors_gracefully`
- [ ] `test_google_oauth_creates_profile_with_google_info`
- [ ] `test_google_oauth_extracts_name_from_google_data`
- [ ] `test_google_oauth_extracts_email_from_google_data`

#### TestGoogleOAuthEdgeCases
- [ ] `test_google_oauth_with_malformed_token_returns_400`
- [ ] `test_google_oauth_with_missing_email_in_google_data_fails`
- [ ] `test_google_oauth_rate_limiting_applied`
- [ ] `test_google_oauth_logs_authentication_attempts`
- [ ] `test_google_oauth_handles_network_timeout_gracefully`
- [ ] `test_google_oauth_handles_google_service_unavailable`

#### TestGoogleOAuthSecurity
- [ ] `test_google_oauth_validates_token_issuer`
- [ ] `test_google_oauth_validates_token_audience`
- [ ] `test_google_oauth_rejects_tampered_tokens`
- [ ] `test_google_oauth_requires_https_in_production`

---

### `test_email_verification.py` - Email Verification

#### TestEmailVerification
- [ ] `test_email_verification_with_valid_token_sets_email_verified_true`
- [ ] `test_email_verification_with_invalid_token_returns_400`
- [ ] `test_email_verification_with_expired_token_returns_400`
- [ ] `test_email_verification_with_already_used_token_returns_400`
- [ ] `test_email_verification_idempotent_for_already_verified_user`
- [ ] `test_email_verification_returns_success_message`
- [ ] `test_email_verification_updates_database_correctly`

#### TestResendVerificationEmail
- [ ] `test_resend_verification_email_with_unverified_user_succeeds`
- [ ] `test_resend_verification_email_with_verified_user_returns_error`
- [ ] `test_resend_verification_email_generates_new_token`
- [ ] `test_resend_verification_email_invalidates_old_token`
- [ ] `test_resend_verification_email_rate_limited`
- [ ] `test_resend_verification_email_requires_authentication`

#### TestEmailVerificationRequiredDecorator
- [ ] `test_verified_user_accesses_protected_endpoint_successfully`
- [ ] `test_unverified_user_blocked_from_protected_endpoint`
- [ ] `test_decorator_returns_403_with_descriptive_error_message`
- [ ] `test_decorator_includes_verification_status_in_response`
- [ ] `test_unauthenticated_user_returns_401_before_verification_check`

#### TestEmailVerificationEmails
- [ ] `test_verification_email_sent_on_registration`
- [ ] `test_verification_email_contains_valid_link`
- [ ] `test_verification_email_contains_user_name`
- [ ] `test_verification_email_multilingual_based_on_user_preference`
- [ ] `test_verification_email_english_template`
- [ ] `test_verification_email_russian_template`
- [ ] `test_verification_email_hebrew_template_rtl`

---

### `test_signals.py` - User Signals

#### TestUserSignals
- [ ] `test_profile_created_automatically_on_user_creation`
- [ ] `test_profile_not_duplicated_on_multiple_saves`
- [ ] `test_welcome_email_sent_on_registration`
- [ ] `test_signal_handlers_rollback_on_error`

---

## 📁 2. RECIPES APP (`apps/recipes/tests/`)

### `test_models.py` - Recipe Models

#### TestCanonicalRecipeModel
- [ ] `test_create_canonical_recipe_with_required_fields_succeeds`
- [ ] `test_create_canonical_recipe_without_name_fails`
- [ ] `test_create_canonical_recipe_without_source_fails`
- [ ] `test_canonical_recipe_unique_constraint_on_name_and_source`
- [ ] `test_canonical_recipe_allows_duplicate_name_with_different_source`
- [ ] `test_canonical_recipe_string_representation_shows_name`
- [ ] `test_canonical_recipe_default_timestamps_auto_set`
- [ ] `test_canonical_recipe_content_jsonfield_stores_rcip_data`
- [ ] `test_canonical_recipe_content_validates_json_structure`
- [ ] `test_canonical_recipe_cook_count_defaults_to_zero`
- [ ] `test_canonical_recipe_cook_count_increments_correctly`
- [ ] `test_canonical_recipe_archived_defaults_to_false`
- [ ] `test_canonical_recipe_category_field_validates_choices`

#### TestUserRecipeModel
- [ ] `test_create_user_recipe_linked_to_user_succeeds`
- [ ] `test_create_user_recipe_linked_to_canonical_recipe`
- [ ] `test_user_recipe_without_user_fails`
- [ ] `test_user_recipe_custom_modifications_stored_in_jsonfield`
- [ ] `test_user_recipe_cascade_deletes_with_user`
- [ ] `test_user_recipe_does_not_cascade_delete_canonical_recipe`
- [ ] `test_user_can_have_multiple_user_recipes`
- [ ] `test_user_recipe_unique_per_user_and_canonical_recipe`
- [ ] `test_user_recipe_notes_field_optional`
- [ ] `test_user_recipe_favorite_flag_defaults_to_false`

#### TestRecipeTranslationModel
- [ ] `test_create_translation_with_pending_status_succeeds`
- [ ] `test_translation_unique_per_recipe_and_language`
- [ ] `test_translation_allows_multiple_languages_per_recipe`
- [ ] `test_translation_status_choices_validated`
- [ ] `test_translation_status_defaults_to_pending`
- [ ] `test_translation_content_jsonfield_stores_translated_data`
- [ ] `test_translation_error_message_stored_on_failure_status`
- [ ] `test_translation_completed_at_timestamp_set_on_completion`
- [ ] `test_translation_retries_increments_on_failed_attempts`
- [ ] `test_translation_cascade_deletes_with_canonical_recipe`

#### TestDiscoveryCacheModel
- [ ] `test_discovery_cache_stores_search_results`
- [ ] `test_discovery_cache_unique_per_language_and_page`
- [ ] `test_discovery_cache_allows_multiple_pages_per_language`
- [ ] `test_discovery_cache_content_jsonfield_stores_recipe_list`
- [ ] `test_discovery_cache_ttl_field_stores_expiry_timestamp`
- [ ] `test_discovery_cache_auto_timestamps`
- [ ] `test_discovery_cache_is_stale_method_checks_ttl`

#### TestRecipeCategoryModel
- [ ] `test_create_recipe_category_with_name`
- [ ] `test_recipe_category_unique_name_constraint`
- [ ] `test_recipe_category_multilingual_name_support`

---

### `test_serializers.py` - Recipe Serializers

#### TestCanonicalRecipeSerializer
- [ ] `test_serializes_recipe_with_all_fields`
- [ ] `test_deserializes_valid_recipe_data`
- [ ] `test_validates_required_fields_present`
- [ ] `test_validates_content_is_valid_json`
- [ ] `test_nested_ingredient_serialization`
- [ ] `test_nested_instruction_serialization`
- [ ] `test_translation_status_included_in_response`
- [ ] `test_translation_status_per_language`
- [ ] `test_cook_count_readonly_field`
- [ ] `test_timestamps_readonly_fields`

#### TestUserRecipeSerializer
- [ ] `test_serializes_user_recipe_with_modifications`
- [ ] `test_includes_canonical_recipe_nested_data`
- [ ] `test_user_field_auto_set_from_request_context`
- [ ] `test_user_field_readonly`
- [ ] `test_modifications_jsonfield_serialization`
- [ ] `test_favorite_flag_serialization`

#### TestRecipeTranslationSerializer
- [ ] `test_serializes_translation_with_status`
- [ ] `test_includes_translated_content`
- [ ] `test_language_code_validated`
- [ ] `test_error_message_included_on_failed_status`
- [ ] `test_completed_at_timestamp_included`

#### TestRCIPSerializer
- [ ] `test_rcip_2_0_format_serialization`
- [ ] `test_rcip_import_creates_recipe_from_valid_json`
- [ ] `test_rcip_export_matches_spec_format`
- [ ] `test_rcip_validation_catches_invalid_format`
- [ ] `test_rcip_validates_required_fields`
- [ ] `test_rcip_validates_ingredient_structure`
- [ ] `test_rcip_validates_instruction_structure`
- [ ] `test_rcip_handles_optional_fields_gracefully`

#### TestIngredientSerializer
- [ ] `test_serializes_ingredient_with_name_and_quantity`
- [ ] `test_validates_quantity_positive_number`
- [ ] `test_validates_unit_field_choices`
- [ ] `test_optional_fields_handled_correctly`

---

### `test_views.py` - Recipe API Views

#### TestRecipeListView
- [ ] `test_list_recipes_returns_paginated_results`
- [ ] `test_list_recipes_default_page_size`
- [ ] `test_list_recipes_custom_page_size_query_param`
- [ ] `test_list_recipes_requires_authentication`
- [ ] `test_list_recipes_unauthenticated_returns_401`
- [ ] `test_list_recipes_filtered_by_language_query_param`
- [ ] `test_list_recipes_includes_translation_status_per_language`
- [ ] `test_list_recipes_search_by_name_query_param`
- [ ] `test_list_recipes_filter_by_category_query_param`
- [ ] `test_list_recipes_filter_by_source_query_param`
- [ ] `test_list_recipes_excludes_archived_by_default`
- [ ] `test_list_recipes_includes_archived_with_query_param`
- [ ] `test_list_recipes_ordering_by_created_date`
- [ ] `test_list_recipes_ordering_by_cook_count`

#### TestRecipeDetailView
- [ ] `test_get_recipe_detail_returns_full_data`
- [ ] `test_get_recipe_detail_requires_authentication`
- [ ] `test_get_recipe_detail_nonexistent_recipe_returns_404`
- [ ] `test_recipe_detail_includes_translation_for_current_language`
- [ ] `test_recipe_detail_translation_status_pending_triggers_background_task`
- [ ] `test_recipe_detail_translation_status_completed_serves_from_cache`
- [ ] `test_recipe_detail_increments_view_count`

#### TestRecipeCreateView
- [ ] `test_create_recipe_with_valid_data_returns_201`
- [ ] `test_create_recipe_creates_record_in_database`
- [ ] `test_create_recipe_requires_authentication`
- [ ] `test_create_recipe_unauthenticated_returns_401`
- [ ] `test_create_recipe_with_invalid_data_returns_400`
- [ ] `test_create_recipe_validates_required_fields`
- [ ] `test_create_recipe_validates_ingredients_structure`
- [ ] `test_create_recipe_validates_instructions_structure`
- [ ] `test_create_recipe_triggers_translation_task_for_all_languages`
- [ ] `test_create_recipe_sets_source_as_user_created`

#### TestRecipeUpdateView
- [ ] `test_update_recipe_with_valid_data_returns_200`
- [ ] `test_update_recipe_changes_persisted_to_database`
- [ ] `test_update_recipe_requires_authentication`
- [ ] `test_update_recipe_requires_ownership_or_admin`
- [ ] `test_update_recipe_by_non_owner_returns_403`
- [ ] `test_update_recipe_invalidates_translation_cache`
- [ ] `test_update_recipe_triggers_retranslation`
- [ ] `test_partial_update_recipe_allowed`

#### TestRecipeDeleteView
- [ ] `test_delete_recipe_requires_authentication`
- [ ] `test_delete_recipe_requires_ownership_or_admin`
- [ ] `test_delete_recipe_by_non_owner_returns_403`
- [ ] `test_delete_recipe_soft_deletes_sets_archived_flag`
- [ ] `test_delete_recipe_removes_from_default_list_view`

#### TestRecipeTranslationView
- [ ] `test_get_translation_with_completed_status_returns_content`
- [ ] `test_get_translation_with_pending_status_returns_status`
- [ ] `test_get_translation_with_failed_status_returns_error_message`
- [ ] `test_request_translation_triggers_background_task`
- [ ] `test_translation_polling_endpoint_returns_current_status`

---

### `test_translation_pipeline.py` - Translation Pipeline

#### TestTranslationOrchestration
- [ ] `test_translation_request_creates_pending_record_in_database`
- [ ] `test_translation_checks_iml_cache_for_ingredient_translations`
- [ ] `test_translation_uses_iml_for_known_ingredients`
- [ ] `test_translation_checks_cooklingo_for_cooking_terms`
- [ ] `test_translation_uses_cooklingo_for_known_terms`
- [ ] `test_translation_falls_back_to_gemini_for_unknown_ingredients`
- [ ] `test_translation_falls_back_to_groq_on_gemini_quota_exceeded`
- [ ] `test_translation_falls_back_to_groq_on_gemini_error`
- [ ] `test_translation_caches_result_in_database`
- [ ] `test_translation_serves_from_cache_on_subsequent_requests`
- [ ] `test_translation_cache_hit_returns_immediately`
- [ ] `test_translation_marks_status_completed_on_success`
- [ ] `test_translation_marks_status_failed_on_error`
- [ ] `test_translation_stores_error_message_on_failure`

#### TestLazyTranslation
- [ ] `test_missing_translation_detected_on_recipe_request`
- [ ] `test_missing_translation_triggers_celery_background_task`
- [ ] `test_translation_status_endpoint_returns_pending_while_processing`
- [ ] `test_translation_status_endpoint_returns_completed_after_processing`
- [ ] `test_translation_polling_frontend_receives_status_updates`
- [ ] `test_lazy_translation_does_not_block_api_response`

#### TestTranslationQuality
- [ ] `test_hebrew_translation_preserves_rtl_formatting`
- [ ] `test_russian_translation_cyrillic_encoding_correct`
- [ ] `test_translation_preserves_recipe_structure`
- [ ] `test_translation_preserves_ingredient_order`
- [ ] `test_translation_preserves_instruction_numbering`
- [ ] `test_measurement_unit_conversion_in_translation`
- [ ] `test_translation_handles_unicode_characters`
- [ ] `test_translation_handles_special_characters`

#### TestTranslationCacheInvalidation
- [ ] `test_recipe_update_invalidates_all_translations`
- [ ] `test_recipe_update_retriggers_translation_tasks`
- [ ] `test_manual_cache_invalidation_endpoint`

---

### `test_rcip_import_export.py` - RCIP Operations

#### TestRCIPImport
- [ ] `test_import_valid_rcip_2_0_json_creates_recipe`
- [ ] `test_import_validates_rcip_version`
- [ ] `test_import_handles_missing_optional_fields`
- [ ] `test_import_validates_required_fields_present`
- [ ] `test_import_validates_ingredient_structure`
- [ ] `test_import_validates_instruction_structure`
- [ ] `test_import_deduplicates_existing_recipes_by_name_and_source`
- [ ] `test_import_creates_new_recipe_if_not_duplicate`
- [ ] `test_import_batch_processes_multiple_recipes`
- [ ] `test_import_rollback_on_validation_error`
- [ ] `test_import_reports_errors_per_recipe`

#### TestRCIPExport
- [ ] `test_export_recipe_as_rcip_2_0_json_format`
- [ ] `test_export_includes_all_required_fields`
- [ ] `test_export_includes_metadata`
- [ ] `test_export_format_validates_against_spec`
- [ ] `test_export_single_recipe_endpoint`
- [ ] `test_bulk_export_all_user_recipes`
- [ ] `test_bulk_export_filtered_recipes`
- [ ] `test_export_respects_user_permissions`

#### TestRCIPValidation
- [ ] `test_validate_rcip_structure_valid_returns_true`
- [ ] `test_validate_rcip_structure_invalid_returns_false_with_errors`
- [ ] `test_validate_rcip_version_supported`
- [ ] `test_validate_rcip_required_fields`
- [ ] `test_validate_rcip_ingredient_quantities`
- [ ] `test_validate_rcip_instruction_order`

---

### `test_ai_generation.py` - AI Recipe Generation

#### TestAIRecipeGeneration
- [ ] `test_generate_recipe_from_ingredients_list_succeeds`
- [ ] `test_generate_recipe_with_dietary_restrictions_applied`
- [ ] `test_generate_recipe_with_cuisine_preference_applied`
- [ ] `test_generate_recipe_with_cooking_time_constraint`
- [ ] `test_generate_recipe_with_difficulty_level_constraint`
- [ ] `test_generation_creates_valid_rcip_format`
- [ ] `test_generation_uses_groq_as_primary_provider`
- [ ] `test_generation_fallback_to_gemini_on_groq_failure`
- [ ] `test_generation_returns_structured_recipe_data`
- [ ] `test_generation_includes_ingredient_quantities`
- [ ] `test_generation_includes_step_by_step_instructions`

#### TestAIRecipeValidation
- [ ] `test_validate_generated_recipe_structure_completeness`
- [ ] `test_validate_ingredient_quantities_are_reasonable`
- [ ] `test_validate_cooking_time_estimates_realistic`
- [ ] `test_validate_instruction_steps_logical_order`
- [ ] `test_validation_rejects_incomplete_recipes`
- [ ] `test_validation_rejects_recipes_with_missing_ingredients`

#### TestAIIngredientExtraction
- [ ] `test_extract_ingredients_from_natural_language_input`
- [ ] `test_normalize_ingredient_names`
- [ ] `test_extract_quantities_and_units`
- [ ] `test_handle_ambiguous_ingredient_descriptions`

---

### `test_discovery_cache.py` - Discovery Cache System

#### TestDiscoveryCacheService
- [ ] `test_cache_stores_search_results_in_redis`
- [ ] `test_cache_key_format_includes_language_and_page`
- [ ] `test_cache_falls_back_to_postgres_on_redis_unavailable`
- [ ] `test_cache_retrieval_from_redis_when_available`
- [ ] `test_cache_retrieval_from_postgres_when_redis_empty`
- [ ] `test_cache_ttl_set_correctly_in_redis`
- [ ] `test_cache_ttl_expires_old_entries_in_redis`
- [ ] `test_cache_per_language_isolation`
- [ ] `test_cache_per_page_number_isolation`

#### TestDiscoveryCacheRefresh
- [ ] `test_periodic_refresh_via_celery_beat_scheduled`
- [ ] `test_periodic_refresh_updates_all_languages`
- [ ] `test_periodic_refresh_updates_multiple_pages`
- [ ] `test_manual_cache_invalidation_clears_redis`
- [ ] `test_manual_cache_invalidation_clears_postgres`
- [ ] `test_selective_language_cache_refresh`
- [ ] `test_cache_refresh_on_new_recipe_added`
- [ ] `test_cache_refresh_handles_errors_gracefully`

#### TestDiscoverySearchIntegration
- [ ] `test_search_uses_cache_when_available`
- [ ] `test_search_performs_live_query_on_cache_miss`
- [ ] `test_search_populates_cache_after_live_query`
- [ ] `test_search_pagination_uses_cached_pages`

---

### `test_recipe_search.py` - Recipe Search & Discovery

#### TestRecipeSearch
- [ ] `test_search_recipes_by_name`
- [ ] `test_search_recipes_by_ingredient`
- [ ] `test_search_recipes_by_category`
- [ ] `test_search_recipes_case_insensitive`
- [ ] `test_search_recipes_partial_match`
- [ ] `test_search_recipes_multilingual_support`
- [ ] `test_search_respects_language_preference`

#### TestRecipeDiscovery
- [ ] `test_discover_recipes_external_api_integration`
- [ ] `test_discover_recipes_web_scraping`
- [ ] `test_discover_recipes_deduplication`
- [ ] `test_discover_recipes_caching_strategy`

---

## 📁 3. SHOPPING APP (`apps/shopping/tests/`)

### `test_models.py` - Shopping Models

#### TestShoppingListModel
- [ ] `test_create_shopping_list_with_owner_succeeds`
- [ ] `test_create_shopping_list_without_owner_fails`
- [ ] `test_shopping_list_name_required`
- [ ] `test_shopping_list_cascade_deletes_items_on_list_delete`
- [ ] `test_shopping_list_does_not_delete_owner_on_list_delete`
- [ ] `test_shopping_list_timestamps_auto_update`
- [ ] `test_shopping_list_archived_flag_defaults_to_false`
- [ ] `test_shopping_list_string_representation`

#### TestShoppingListItemModel
- [ ] `test_create_item_with_required_fields_succeeds`
- [ ] `test_create_item_without_shopping_list_fails`
- [ ] `test_item_name_required`
- [ ] `test_item_quantity_validates_positive_number`
- [ ] `test_item_quantity_defaults_to_one`
- [ ] `test_item_unit_field_optional`
- [ ] `test_item_checked_defaults_to_false`
- [ ] `test_item_added_by_user_tracked`
- [ ] `test_item_checked_by_user_tracked`
- [ ] `test_item_timestamps_auto_set`
- [ ] `test_item_cascade_deletes_with_shopping_list`

#### TestShoppingListCollaboratorModel
- [ ] `test_add_collaborator_with_permission_level_succeeds`
- [ ] `test_collaborator_requires_shopping_list`
- [ ] `test_collaborator_requires_user`
- [ ] `test_collaborator_unique_per_list_and_user`
- [ ] `test_collaborator_duplicate_raises_integrity_error`
- [ ] `test_permission_level_choices_validated`
- [ ] `test_permission_level_defaults_to_view`
- [ ] `test_collaborator_cascade_deletes_with_list`
- [ ] `test_collaborator_does_not_delete_user_on_removal`
- [ ] `test_collaborator_timestamps_auto_set`

#### TestShoppingListShareKeyModel
- [ ] `test_share_key_generated_unique`
- [ ] `test_share_key_uuid_format`
- [ ] `test_share_key_linked_to_shopping_list`
- [ ] `test_share_key_expiry_timestamp_set`
- [ ] `test_share_key_single_use_flag_defaults_to_false`
- [ ] `test_share_key_used_flag_defaults_to_false`
- [ ] `test_share_key_created_by_user_tracked`
- [ ] `test_share_key_is_expired_method_checks_timestamp`
- [ ] `test_share_key_cascade_deletes_with_list`

---

### `test_serializers.py` - Shopping Serializers

#### TestShoppingListSerializer
- [ ] `test_serializes_list_with_all_fields`
- [ ] `test_serializes_items_nested`
- [ ] `test_serializes_collaborators_count`
- [ ] `test_serializes_owner_details`
- [ ] `test_serializes_user_permission_level`
- [ ] `test_deserializes_valid_list_data`
- [ ] `test_owner_field_readonly`
- [ ] `test_timestamps_readonly`

#### TestShoppingListItemSerializer
- [ ] `test_serializes_item_with_all_fields`
- [ ] `test_validates_quantity_positive`
- [ ] `test_validates_quantity_not_zero`
- [ ] `test_added_by_user_readonly`
- [ ] `test_checked_by_user_readonly`
- [ ] `test_shopping_list_field_required_on_create`

#### TestShoppingListCollaboratorSerializer
- [ ] `test_serializes_collaborator_with_user_details`
- [ ] `test_permission_level_validated`
- [ ] `test_shopping_list_field_readonly`
- [ ] `test_user_field_required`

---

### `test_views.py` - Shopping API Views

#### TestShoppingListViewSet
- [ ] `test_list_shopping_lists_returns_owned_lists`
- [ ] `test_list_shopping_lists_returns_collaborated_lists`
- [ ] `test_list_shopping_lists_requires_authentication`
- [ ] `test_list_shopping_lists_paginated`
- [ ] `test_create_shopping_list_sets_current_user_as_owner`
- [ ] `test_create_shopping_list_requires_authentication`
- [ ] `test_create_shopping_list_returns_201`
- [ ] `test_update_shopping_list_requires_edit_permission`
- [ ] `test_update_shopping_list_by_viewer_returns_403`
- [ ] `test_delete_shopping_list_requires_owner`
- [ ] `test_delete_shopping_list_by_collaborator_returns_403`
- [ ] `test_archive_shopping_list_endpoint_sets_archived_flag`
- [ ] `test_restore_shopping_list_endpoint_unsets_archived_flag`

#### TestShoppingListItemViewSet
- [ ] `test_list_items_returns_all_items_for_list`
- [ ] `test_list_items_requires_list_access_permission`
- [ ] `test_add_item_to_list_requires_edit_permission`
- [ ] `test_add_item_to_list_creates_record`
- [ ] `test_add_item_by_viewer_returns_403`
- [ ] `test_update_item_requires_edit_permission`
- [ ] `test_update_item_changes_persisted`
- [ ] `test_check_item_updates_checked_status_to_true`
- [ ] `test_uncheck_item_updates_checked_status_to_false`
- [ ] `test_check_item_tracks_user_who_checked`
- [ ] `test_delete_item_requires_edit_permission`
- [ ] `test_bulk_add_items_from_recipe_creates_multiple_items`
- [ ] `test_bulk_add_items_requires_edit_permission`

#### TestShoppingListCollaborationViewSet
- [ ] `test_add_collaborator_requires_owner_permission`
- [ ] `test_add_collaborator_creates_record`
- [ ] `test_add_collaborator_by_non_owner_returns_403`
- [ ] `test_generate_share_link_creates_share_key`
- [ ] `test_generate_share_link_requires_owner_or_editor`
- [ ] `test_generate_share_link_returns_key_and_expiry`
- [ ] `test_join_via_share_key_adds_user_as_collaborator`
- [ ] `test_join_via_expired_key_returns_400`
- [ ] `test_join_via_used_single_use_key_returns_400`
- [ ] `test_join_via_invalid_key_returns_404`
- [ ] `test_remove_collaborator_requires_owner`
- [ ] `test_remove_collaborator_deletes_record`
- [ ] `test_owner_cannot_remove_self`
- [ ] `test_update_collaborator_permission_level_requires_owner`
- [ ] `test_update_permission_level_changes_persisted`

---

### `test_websocket_consumers.py` - WebSocket Consumers

#### TestShoppingListConsumer
- [ ] `test_websocket_connect_requires_authentication`
- [ ] `test_websocket_connect_with_valid_auth_succeeds`
- [ ] `test_websocket_connect_adds_user_to_group`
- [ ] `test_websocket_connect_group_name_based_on_list_id`
- [ ] `test_websocket_connect_without_auth_rejected`
- [ ] `test_websocket_disconnect_removes_from_group`
- [ ] `test_item_added_event_broadcasts_to_all_collaborators`
- [ ] `test_item_checked_event_broadcasts_update`
- [ ] `test_item_unchecked_event_broadcasts_update`
- [ ] `test_item_deleted_event_broadcasts_update`
- [ ] `test_list_updated_event_broadcasts_changes`
- [ ] `test_collaborator_joined_event_broadcasts_to_group`
- [ ] `test_collaborator_left_event_broadcasts_to_group`
- [ ] `test_broadcast_includes_user_info_who_made_change`
- [ ] `test_broadcast_includes_timestamp`

#### TestWebSocketPermissions
- [ ] `test_unauthenticated_connection_rejected`
- [ ] `test_user_without_list_permission_cannot_join_group`
- [ ] `test_user_with_view_permission_receives_broadcasts`
- [ ] `test_user_with_view_permission_cannot_send_updates`
- [ ] `test_user_with_edit_permission_can_send_updates`
- [ ] `test_removed_collaborator_disconnected_from_group`

#### TestWebSocketMessageFormat
- [ ] `test_message_format_includes_event_type`
- [ ] `test_message_format_includes_payload`
- [ ] `test_message_format_json_serializable`
- [ ] `test_error_messages_have_error_field`

---

### `test_collaboration.py` - Shopping List Collaboration

#### TestListSharing
- [ ] `test_owner_shares_list_with_collaborator_via_email`
- [ ] `test_owner_shares_list_with_collaborator_via_share_link`
- [ ] `test_collaborator_receives_notification_on_share`
- [ ] `test_collaborator_receives_realtime_updates_via_websocket`
- [ ] `test_collaborator_with_edit_permission_can_add_items`
- [ ] `test_collaborator_with_edit_permission_can_check_items`
- [ ] `test_collaborator_with_view_permission_can_only_read`
- [ ] `test_collaborator_with_view_permission_cannot_modify`
- [ ] `test_remove_collaborator_revokes_access_immediately`
- [ ] `test_removed_collaborator_loses_websocket_connection`

#### TestShareKeyFlow
- [ ] `test_generate_share_key_creates_unique_token`
- [ ] `test_generate_share_key_sets_expiry_24_hours_default`
- [ ] `test_generate_share_key_custom_expiry_time`
- [ ] `test_share_key_expiry_prevents_access_after_expiration`
- [ ] `test_single_use_key_marked_used_after_first_use`
- [ ] `test_single_use_key_invalidates_after_first_use`
- [ ] `test_multi_use_key_allows_multiple_joins`
- [ ] `test_join_with_valid_key_adds_to_collaborators`
- [ ] `test_join_with_valid_key_sets_default_permission_level`
- [ ] `test_list_all_active_share_keys_for_list`
- [ ] `test_revoke_share_key_invalidates_immediately`

#### TestCollaborationNotifications
- [ ] `test_collaborator_added_sends_email_notification`
- [ ] `test_collaborator_removed_sends_email_notification`
- [ ] `test_permission_changed_sends_notification`
- [ ] `test_item_added_sends_push_notification_to_collaborators`

---

### `test_permissions.py` - Shopping Permissions

#### TestShoppingListPermissions
- [ ] `test_owner_has_full_access_to_list`
- [ ] `test_owner_can_read_list`
- [ ] `test_owner_can_edit_list`
- [ ] `test_owner_can_delete_list`
- [ ] `test_owner_can_manage_collaborators`
- [ ] `test_editor_can_read_list`
- [ ] `test_editor_can_add_items`
- [ ] `test_editor_can_edit_items`
- [ ] `test_editor_can_delete_items`
- [ ] `test_editor_cannot_delete_list`
- [ ] `test_editor_cannot_manage_collaborators`
- [ ] `test_viewer_can_only_read_list`
- [ ] `test_viewer_cannot_add_items`
- [ ] `test_viewer_cannot_edit_items`
- [ ] `test_viewer_cannot_delete_items`
- [ ] `test_non_collaborator_cannot_access_list`
- [ ] `test_non_collaborator_get_returns_404`

#### TestIsShoppingListOwner
- [ ] `test_owner_permission_check_passes`
- [ ] `test_non_owner_permission_check_fails`

#### TestHasShoppingListAccess
- [ ] `test_collaborator_has_access`
- [ ] `test_non_collaborator_no_access`

---

### `test_archive_workflows.py` - Archive Workflows

#### TestArchiveFlow
- [ ] `test_archive_list_sets_archived_flag_to_true`
- [ ] `test_archive_list_preserves_all_data`
- [ ] `test_archived_lists_excluded_from_default_queries`
- [ ] `test_archived_lists_visible_with_archived_filter`
- [ ] `test_restore_archived_list_unsets_archived_flag`
- [ ] `test_restore_archived_list_returns_to_default_queries`
- [ ] `test_permanently_delete_archived_list_after_30_days`
- [ ] `test_permanently_delete_removes_all_related_data`
- [ ] `test_archive_cascade_archives_all_items`
- [ ] `test_restore_cascade_restores_all_items`

#### TestArchiveAutomation
- [ ] `test_auto_archive_completed_lists_after_7_days`
- [ ] `test_auto_delete_archived_lists_after_30_days`
- [ ] `test_celery_task_scheduled_for_archive_cleanup`

---

## 📁 4. NUTRITION APP (`apps/nutrition/tests/`)

### `test_models.py` - Nutrition Models

#### TestNutritionEntryModel
- [ ] `test_create_entry_with_user_and_date_succeeds`
- [ ] `test_create_entry_without_user_fails`
- [ ] `test_entry_date_defaults_to_today`
- [ ] `test_entry_meal_type_choices_validated`
- [ ] `test_entry_calories_field_positive_number`
- [ ] `test_entry_protein_field_positive_number`
- [ ] `test_entry_carbs_field_positive_number`
- [ ] `test_entry_fat_field_positive_number`
- [ ] `test_entry_macros_calculated_correctly`
- [ ] `test_entry_timestamps_auto_set`
- [ ] `test_entry_cascade_deletes_with_user`

#### TestMealLogModel
- [ ] `test_create_meal_log_with_nutrition_entry`
- [ ] `test_meal_log_description_required`
- [ ] `test_meal_log_ai_generated_flag`
- [ ] `test_meal_log_confidence_score`

#### TestStreakModel
- [ ] `test_streak_created_for_user`
- [ ] `test_streak_count_defaults_to_zero`
- [ ] `test_streak_increments_on_consecutive_days_logging`
- [ ] `test_streak_resets_on_missed_day`
- [ ] `test_streak_last_logged_date_updated`
- [ ] `test_streak_longest_streak_tracked`

#### TestBadgeModel
- [ ] `test_badge_awarded_on_milestone_achievement`
- [ ] `test_badge_types_validated`
- [ ] `test_badge_unique_per_user_and_type`
- [ ] `test_badge_awarded_date_auto_set`

#### TestNutritionGoalModel
- [ ] `test_create_nutrition_goal_for_user`
- [ ] `test_goal_daily_calorie_target`
- [ ] `test_goal_macro_targets`
- [ ] `test_goal_one_per_user`

---

### `test_serializers.py` - Nutrition Serializers

#### TestNutritionEntrySerializer
- [ ] `test_serializes_entry_with_all_fields`
- [ ] `test_validates_calories_positive`
- [ ] `test_validates_macros_positive`
- [ ] `test_user_field_auto_set_from_context`
- [ ] `test_date_defaults_to_today`

#### TestMealLogSerializer
- [ ] `test_serializes_meal_log_with_description`
- [ ] `test_includes_nutrition_entry_nested`
- [ ] `test_ai_generated_flag_serialization`

---

### `test_views.py` - Nutrition API Views

#### TestNutritionEntryViewSet
- [ ] `test_list_nutrition_entries_requires_authentication`
- [ ] `test_list_entries_returns_user_entries_only`
- [ ] `test_list_entries_filtered_by_date_range`
- [ ] `test_create_nutrition_entry_with_valid_data_returns_201`
- [ ] `test_create_entry_requires_authentication`
- [ ] `test_update_entry_requires_ownership`
- [ ] `test_delete_entry_requires_ownership`
- [ ] `test_get_daily_summary_aggregates_entries_by_date`
- [ ] `test_get_weekly_summary_aggregates_entries_by_week`

#### TestMealLogViewSet
- [ ] `test_log_meal_creates_entry_and_meal_log`
- [ ] `test_log_meal_with_ai_parsing_enabled`
- [ ] `test_log_meal_manual_entry`

#### TestNutritionDashboardView
- [ ] `test_dashboard_requires_authentication`
- [ ] `test_dashboard_returns_weekly_summary`
- [ ] `test_dashboard_includes_daily_calorie_totals`
- [ ] `test_dashboard_includes_macro_breakdown`
- [ ] `test_dashboard_includes_streak_info`
- [ ] `test_dashboard_includes_badges_earned`
- [ ] `test_dashboard_includes_goal_progress`

#### TestNutritionGoalView
- [ ] `test_get_nutrition_goal_returns_user_goal`
- [ ] `test_set_nutrition_goal_creates_or_updates`
- [ ] `test_goal_requires_authentication`

---

### `test_ai_logging.py` - AI Meal Logging

#### TestAIMealLogging
- [ ] `test_log_meal_with_natural_language_input_succeeds`
- [ ] `test_ai_extracts_meal_components_from_description`
- [ ] `test_ai_estimates_calories_for_meal`
- [ ] `test_ai_estimates_macros_for_meal`
- [ ] `test_ai_handles_ambiguous_inputs_gracefully`
- [ ] `test_ai_handles_multi_food_descriptions`
- [ ] `test_ai_handles_portion_sizes`
- [ ] `test_ai_parsing_fallback_on_failure`
- [ ] `test_ai_confidence_score_included_in_response`

#### TestAIMealExtractionAccuracy
- [ ] `test_extract_calories_from_common_foods`
- [ ] `test_extract_protein_content_accurately`
- [ ] `test_extract_carbs_content_accurately`
- [ ] `test_extract_fat_content_accurately`
- [ ] `test_handle_unknown_foods_gracefully`

---

### `test_analytics.py` - Nutrition Analytics

#### TestNutritionAnalytics
- [ ] `test_calculate_average_daily_calories_over_period`
- [ ] `test_calculate_average_daily_protein`
- [ ] `test_calculate_average_daily_carbs`
- [ ] `test_calculate_average_daily_fat`
- [ ] `test_macro_distribution_chart_data_format`
- [ ] `test_macro_distribution_percentages_sum_to_100`
- [ ] `test_weekly_trend_analysis_shows_changes`
- [ ] `test_calorie_deficit_or_surplus_calculation`
- [ ] `test_goal_adherence_percentage`

#### TestStreakAnalytics
- [ ] `test_current_streak_calculation`
- [ ] `test_longest_streak_tracked`
- [ ] `test_streak_broken_notification`

---

## 📁 5. CORE APP (`apps/core/tests/`)

### `test_iml_service.py` - IML Service

#### TestIMLService
- [ ] `test_service_initialization_loads_ingredients_from_database`
- [ ] `test_service_initialization_builds_cache`
- [ ] `test_lookup_ingredient_returns_translations_for_all_languages`
- [ ] `test_lookup_ingredient_english_to_russian`
- [ ] `test_lookup_ingredient_english_to_hebrew`
- [ ] `test_lookup_ingredient_russian_to_english`
- [ ] `test_lookup_ingredient_hebrew_to_english`
- [ ] `test_lookup_nonexistent_ingredient_returns_none`
- [ ] `test_lookup_case_insensitive`
- [ ] `test_lookup_handles_plurals`
- [ ] `test_add_ingredient_adds_to_library_and_cache`
- [ ] `test_add_ingredient_with_all_languages`
- [ ] `test_add_duplicate_ingredient_updates_existing`
- [ ] `test_reload_refreshes_cache_from_database`
- [ ] `test_service_thread_safe`
- [ ] `test_cache_performance_lookup_under_1ms`

#### TestIMLDataManagement
- [ ] `test_import_ingredients_from_csv`
- [ ] `test_export_ingredients_to_csv`
- [ ] `test_bulk_add_ingredients`
- [ ] `test_ingredient_validation_on_add`

---

### `test_cooklingo_service.py` - CookLingo Service

#### TestCookLingoService
- [ ] `test_service_initialization_loads_cooking_terms_from_database`
- [ ] `test_service_initialization_builds_cache`
- [ ] `test_lookup_cooking_term_returns_translations`
- [ ] `test_lookup_cooking_term_english_to_russian`
- [ ] `test_lookup_cooking_term_english_to_hebrew`
- [ ] `test_lookup_nonexistent_term_returns_none`
- [ ] `test_lookup_case_insensitive`
- [ ] `test_lookup_handles_verb_forms`
- [ ] `test_add_term_adds_to_glossary_and_cache`
- [ ] `test_add_term_with_all_languages`
- [ ] `test_reload_refreshes_cache_from_database`
- [ ] `test_service_thread_safe`

#### TestCookLingoCategories
- [ ] `test_terms_categorized_by_type`
- [ ] `test_lookup_by_category`
- [ ] `test_cooking_methods_category`
- [ ] `test_kitchen_equipment_category`

---

### `test_translation_service.py` - Smart Translation Service

#### TestSmartTranslationService
- [ ] `test_translate_recipe_with_iml_cache_hit_fast_response`
- [ ] `test_translate_ingredient_uses_iml_when_available`
- [ ] `test_translate_cooking_term_uses_cooklingo_when_available`
- [ ] `test_translate_unknown_ingredient_falls_back_to_gemini`
- [ ] `test_translate_falls_back_to_groq_on_gemini_quota_exceeded`
- [ ] `test_translate_falls_back_to_groq_on_gemini_error`
- [ ] `test_translation_result_stored_in_database_cache`
- [ ] `test_translation_cache_lookup_before_api_call`
- [ ] `test_translation_respects_rtl_for_hebrew`
- [ ] `test_translation_preserves_structure`
- [ ] `test_translation_handles_mixed_content`
- [ ] `test_concurrent_translation_requests_deduplicated`

#### TestTranslationFallbackLogic
- [ ] `test_gemini_primary_provider_called_first`
- [ ] `test_groq_fallback_on_gemini_quota_error`
- [ ] `test_groq_fallback_on_gemini_network_error`
- [ ] `test_groq_fallback_on_gemini_timeout`
- [ ] `test_all_providers_fail_returns_error`
- [ ] `test_fallback_logged_for_monitoring`

#### TestTranslationCaching
- [ ] `test_cache_key_format_includes_language_and_content_hash`
- [ ] `test_cache_hit_returns_immediately`
- [ ] `test_cache_miss_triggers_translation_and_stores_result`
- [ ] `test_cache_ttl_set_appropriately`
- [ ] `test_cache_invalidation_on_source_update`

---

### `test_ingredient_mapper.py` - Ingredient Mapper

#### TestIngredientMapper
- [ ] `test_map_ingredient_normalizes_name`
- [ ] `test_map_ingredient_removes_extra_whitespace`
- [ ] `test_map_ingredient_lowercases_name`
- [ ] `test_map_ingredient_handles_plurals_to_singular`
- [ ] `test_map_ingredient_handles_synonyms`
- [ ] `test_map_ingredient_handles_spelling_variations`
- [ ] `test_map_ingredient_returns_canonical_form`
- [ ] `test_map_unknown_ingredient_returns_original`

#### TestIngredientNormalization
- [ ] `test_normalize_removes_articles`
- [ ] `test_normalize_handles_unicode_characters`
- [ ] `test_normalize_handles_diacritics`
- [ ] `test_normalize_preserves_meaningful_punctuation`

---

### `test_unit_converter.py` - Unit Converter

#### TestUnitConverter
- [ ] `test_convert_volume_cups_to_ml`
- [ ] `test_convert_volume_tablespoons_to_ml`
- [ ] `test_convert_volume_teaspoons_to_ml`
- [ ] `test_convert_volume_liters_to_cups`
- [ ] `test_convert_weight_grams_to_ounces`
- [ ] `test_convert_weight_kilograms_to_pounds`
- [ ] `test_convert_weight_ounces_to_grams`
- [ ] `test_convert_temperature_celsius_to_fahrenheit`
- [ ] `test_convert_temperature_fahrenheit_to_celsius`
- [ ] `test_convert_invalid_units_raises_error`
- [ ] `test_convert_incompatible_units_raises_error`
- [ ] `test_convert_preserves_precision`

#### TestUnitValidation
- [ ] `test_validate_volume_units`
- [ ] `test_validate_weight_units`
- [ ] `test_validate_temperature_units`
- [ ] `test_invalid_unit_returns_false`

---

### `test_rcip_validators.py` - RCIP Validators

#### TestRCIPValidator
- [ ] `test_validate_rcip_2_0_structure_valid_returns_true`
- [ ] `test_validate_rcip_structure_invalid_returns_false`
- [ ] `test_validate_required_fields_present`
- [ ] `test_validate_version_field_matches_2_0`
- [ ] `test_validate_metadata_section_present`
- [ ] `test_validate_ingredients_array_present`
- [ ] `test_validate_instructions_array_present`
- [ ] `test_validate_ingredient_has_name`
- [ ] `test_validate_ingredient_has_quantity`
- [ ] `test_validate_ingredient_quantity_positive`
- [ ] `test_validate_instruction_has_step_number`
- [ ] `test_validate_instruction_has_description`
- [ ] `test_validation_errors_descriptive_and_actionable`
- [ ] `test_validate_nutrition_info_optional`
- [ ] `test_validate_prep_time_optional`
- [ ] `test_validate_cook_time_optional`

#### TestRCIPSchemaValidation
- [ ] `test_validate_against_json_schema`
- [ ] `test_schema_catches_missing_required_fields`
- [ ] `test_schema_catches_invalid_data_types`

---

## 📁 6. AI_AGENTS APP (`apps/ai_agents/tests/`)

### `test_groq_integration.py` - Groq Integration

#### TestGroqClient
- [ ] `test_groq_client_initialization_with_api_key`
- [ ] `test_groq_client_initialization_without_api_key_raises_error`
- [ ] `test_send_prompt_returns_response`
- [ ] `test_send_prompt_with_system_message`
- [ ] `test_send_prompt_with_temperature_parameter`
- [ ] `test_send_prompt_with_max_tokens_parameter`
- [ ] `test_handle_rate_limiting_retries_with_backoff`
- [ ] `test_handle_api_errors_gracefully`
- [ ] `test_handle_network_timeout_raises_appropriate_error`
- [ ] `test_retry_logic_on_temporary_500_errors`
- [ ] `test_max_retries_exceeded_raises_error`

#### TestGroqRecipeGeneration
- [ ] `test_generate_recipe_with_groq_returns_structured_data`
- [ ] `test_generate_recipe_uses_llama_3_1_model`
- [ ] `test_generate_recipe_prompt_includes_ingredients`
- [ ] `test_generate_recipe_prompt_includes_dietary_restrictions`
- [ ] `test_response_parsing_to_rcip_format`
- [ ] `test_response_parsing_handles_json_errors`

#### TestGroqModels
- [ ] `test_llama_3_1_70b_model_available`
- [ ] `test_llama_3_3_70b_model_available`
- [ ] `test_model_selection_based_on_task_complexity`

---

### `test_gemini_integration.py` - Gemini Integration

#### TestGeminiClient
- [ ] `test_gemini_client_initialization_with_api_key`
- [ ] `test_gemini_client_initialization_without_api_key_raises_error`
- [ ] `test_translate_recipe_with_gemini_returns_translation`
- [ ] `test_translate_uses_flash_2_0_lite_model`
- [ ] `test_handle_quota_exceeded_error_raises_specific_exception`
- [ ] `test_handle_rate_limit_error`
- [ ] `test_handle_api_errors_gracefully`
- [ ] `test_handle_network_timeout`
- [ ] `test_retry_logic_on_temporary_errors`

#### TestGeminiTranslation
- [ ] `test_translate_preserves_recipe_structure`
- [ ] `test_translate_handles_rtl_hebrew`
- [ ] `test_translate_handles_cyrillic_russian`
- [ ] `test_translate_prompt_includes_context`

---

### `test_anthropic_integration.py` - Anthropic Integration

#### TestAnthropicClient
- [ ] `test_anthropic_client_initialization_with_api_key`
- [ ] `test_send_prompt_returns_response`
- [ ] `test_uses_claude_sonnet_model`
- [ ] `test_handle_api_errors`

---

### `test_agent_orchestration.py` - Agent Orchestration

#### TestUniversalAgentAPI
- [ ] `test_agent_routes_recipe_generation_to_groq`
- [ ] `test_agent_routes_translation_to_gemini`
- [ ] `test_agent_routes_validation_to_appropriate_provider`
- [ ] `test_agent_handles_multi_provider_fallback`
- [ ] `test_agent_caches_responses_in_database`
- [ ] `test_agent_cache_hit_returns_immediately`
- [ ] `test_agent_tracks_provider_usage_stats`
- [ ] `test_agent_switches_provider_on_quota_exceeded`

#### TestAgentTaskQueue
- [ ] `test_task_queued_for_async_processing`
- [ ] `test_task_status_tracked`
- [ ] `test_task_result_stored_on_completion`
- [ ] `test_task_error_stored_on_failure`

---

### `test_prompt_templates.py` - Prompt Templates

#### TestPromptTemplates
- [ ] `test_recipe_generation_prompt_structure_includes_ingredients`
- [ ] `test_recipe_generation_prompt_includes_constraints`
- [ ] `test_translation_prompt_includes_source_language`
- [ ] `test_translation_prompt_includes_target_language`
- [ ] `test_translation_prompt_includes_context`
- [ ] `test_validation_prompt_includes_criteria`
- [ ] `test_validation_prompt_includes_recipe_data`
- [ ] `test_prompt_template_variable_substitution`

#### TestPromptEngineering
- [ ] `test_system_prompt_sets_appropriate_role`
- [ ] `test_user_prompt_provides_clear_instructions`
- [ ] `test_few_shot_examples_included_when_appropriate`
- [ ] `test_prompt_length_within_token_limits`

---

### `test_fallback_logic.py` - Provider Fallback

#### TestProviderFallback
- [ ] `test_fallback_from_gemini_to_groq_on_quota_exceeded`
- [ ] `test_fallback_from_groq_to_gemini_on_rate_limit`
- [ ] `test_fallback_from_primary_to_secondary_on_error`
- [ ] `test_fallback_chain_tries_all_providers`
- [ ] `test_all_providers_fail_returns_descriptive_error`
- [ ] `test_fallback_logged_for_monitoring`
- [ ] `test_fallback_preserves_request_context`

#### TestFallbackStrategies
- [ ] `test_immediate_fallback_on_quota_error`
- [ ] `test_retry_before_fallback_on_network_error`
- [ ] `test_circuit_breaker_prevents_repeated_failing_provider_calls`

---

## 📁 7. LEGAL APP (`apps/legal/tests/`)

### `test_models.py` - Legal Models

#### TestLegalAcceptance
- [ ] `test_create_legal_acceptance_record_succeeds`
- [ ] `test_acceptance_requires_user`
- [ ] `test_acceptance_requires_document_type`
- [ ] `test_acceptance_requires_version`
- [ ] `test_acceptance_timestamp_auto_set`
- [ ] `test_acceptance_ip_address_tracked`
- [ ] `test_acceptance_user_agent_tracked`
- [ ] `test_acceptance_unique_per_user_document_version`
- [ ] `test_acceptance_cascade_deletes_with_user`

#### TestLegalDocument
- [ ] `test_legal_document_versions_tracked`
- [ ] `test_legal_document_content_stored`
- [ ] `test_legal_document_multilingual_support`

---

### `test_views.py` - Legal API Views

#### TestLegalDocumentViews
- [ ] `test_get_terms_of_service_in_english_returns_200`
- [ ] `test_get_terms_of_service_in_russian_returns_200`
- [ ] `test_get_terms_of_service_in_hebrew_returns_200`
- [ ] `test_get_privacy_policy_in_english`
- [ ] `test_get_privacy_policy_in_russian`
- [ ] `test_get_privacy_policy_in_hebrew`
- [ ] `test_get_cookie_policy_in_english`
- [ ] `test_get_cookie_policy_in_russian`
- [ ] `test_get_cookie_policy_in_hebrew`
- [ ] `test_get_copyright_notice_in_english`
- [ ] `test_get_rcip_license_in_english`
- [ ] `test_legal_document_includes_version_number`
- [ ] `test_legal_document_includes_effective_date`
- [ ] `test_invalid_language_returns_default_english`

#### TestLegalAcceptanceView
- [ ] `test_record_acceptance_creates_entry_in_database`
- [ ] `test_record_acceptance_requires_authentication`
- [ ] `test_record_acceptance_unauthenticated_returns_401`
- [ ] `test_record_acceptance_includes_document_type`
- [ ] `test_record_acceptance_includes_version`
- [ ] `test_record_acceptance_tracks_ip_address`
- [ ] `test_record_acceptance_tracks_user_agent`
- [ ] `test_record_acceptance_returns_201`

---

### `test_gdpr_compliance.py` - GDPR Compliance

#### TestDataExport
- [ ] `test_user_can_request_data_export`
- [ ] `test_data_export_requires_authentication`
- [ ] `test_export_includes_all_user_profile_data`
- [ ] `test_export_includes_all_user_recipes`
- [ ] `test_export_includes_all_shopping_lists`
- [ ] `test_export_includes_all_nutrition_entries`
- [ ] `test_export_includes_legal_acceptances`
- [ ] `test_export_format_is_json`
- [ ] `test_export_json_structure_well_formed`
- [ ] `test_export_excludes_sensitive_data_of_others`
- [ ] `test_export_generation_queued_as_celery_task`
- [ ] `test_export_download_link_sent_via_email`
- [ ] `test_export_download_link_expires_after_48_hours`

#### TestDataDeletion
- [ ] `test_user_can_request_account_deletion`
- [ ] `test_deletion_requires_authentication`
- [ ] `test_deletion_has_30_day_grace_period`
- [ ] `test_deletion_sets_account_inactive_immediately`
- [ ] `test_deletion_scheduled_as_celery_task`
- [ ] `test_deletion_removes_all_personal_data_after_grace_period`
- [ ] `test_deletion_anonymizes_contributed_content`
- [ ] `test_deletion_removes_profile_data`
- [ ] `test_deletion_removes_authentication_data`
- [ ] `test_deletion_removes_shopping_lists`
- [ ] `test_deletion_removes_nutrition_entries`
- [ ] `test_deletion_preserves_canonical_recipes_anonymously`
- [ ] `test_deletion_cancellation_during_grace_period_restores_account`
- [ ] `test_deletion_confirmation_email_sent`

#### TestCookieConsent
- [ ] `test_cookie_consent_preferences_stored`
- [ ] `test_cookie_consent_updated`
- [ ] `test_cookie_consent_includes_essential_functional_analytics`
- [ ] `test_gpc_signal_detection_respected`

---

## 📁 8. INTEGRATION TESTS (`tests/integration/`)

### `test_recipe_to_shopping.py` - Recipe to Shopping Integration

#### TestRecipeToShoppingFlow
- [ ] `test_add_recipe_ingredients_to_shopping_list_creates_items`
- [ ] `test_ingredient_quantities_calculated_for_servings`
- [ ] `test_ingredient_quantities_scaled_correctly`
- [ ] `test_duplicate_ingredients_merged_in_shopping_list`
- [ ] `test_duplicate_ingredients_quantities_summed`
- [ ] `test_ingredient_units_normalized_before_merging`
- [ ] `test_recipe_link_stored_with_shopping_list_item`
- [ ] `test_multiple_recipes_added_to_same_list`

---

### `test_auth_flow_complete.py` - Complete Auth Flow

#### TestEndToEndAuthFlow
- [ ] `test_registration_verification_login_profile_update_logout_complete_flow`
- [ ] `test_registration_creates_user_with_unverified_email`
- [ ] `test_verification_email_sent_and_contains_valid_token`
- [ ] `test_email_verification_enables_protected_resource_access`
- [ ] `test_login_with_verified_account_returns_tokens`
- [ ] `test_profile_update_persists_changes`
- [ ] `test_logout_invalidates_tokens`
- [ ] `test_google_oauth_login_to_protected_resource_access`
- [ ] `test_google_oauth_automatically_verified`
- [ ] `test_password_reset_flow_complete_from_request_to_new_password`

---

### `test_translation_pipeline.py` - Translation Pipeline Integration

#### TestTranslationPipelineIntegration
- [ ] `test_recipe_creation_triggers_translation_jobs_for_all_languages`
- [ ] `test_translation_jobs_queued_in_celery`
- [ ] `test_translation_cache_hit_serves_instantly`
- [ ] `test_translation_cache_miss_triggers_background_job`
- [ ] `test_translation_status_polling_returns_pending_then_completed`
- [ ] `test_translation_completion_updates_database_record`
- [ ] `test_frontend_receives_completed_translation`
- [ ] `test_multiple_concurrent_translation_requests_handled`

---

### `test_ai_workflow.py` - AI Workflow Integration

#### TestCompleteAIWorkflow
- [ ] `test_generate_recipe_translate_add_to_shopping_complete_flow`
- [ ] `test_user_provides_ingredients_list`
- [ ] `test_ai_generates_recipe_from_ingredients`
- [ ] `test_generated_recipe_automatically_translated`
- [ ] `test_user_adds_recipe_to_shopping_list`
- [ ] `test_discover_recipe_scrape_validate_import_flow`
- [ ] `test_user_searches_recipes_externally`
- [ ] `test_recipe_scraped_from_web`
- [ ] `test_scraped_recipe_validated`
- [ ] `test_validated_recipe_imported_to_system`

---

## 📁 9. E2E TESTS (`tests/e2e/`)

### `test_user_journey_new_user.py` - New User Journey

#### TestNewUserOnboarding
- [ ] `test_new_user_registers_verifies_email_explores_recipes_complete_journey`
- [ ] `test_new_user_visits_homepage`
- [ ] `test_new_user_clicks_register`
- [ ] `test_new_user_fills_registration_form`
- [ ] `test_new_user_receives_verification_email`
- [ ] `test_new_user_clicks_verification_link`
- [ ] `test_new_user_redirected_to_dashboard`
- [ ] `test_new_user_explores_discover_page`
- [ ] `test_new_user_saves_recipe_to_profile`
- [ ] `test_google_oauth_login_immediate_access`

---

### `test_user_journey_recipe_discovery.py` - Recipe Discovery Journey

#### TestRecipeDiscoveryJourney
- [ ] `test_user_searches_discovers_recipe_saves_to_profile`
- [ ] `test_user_enters_search_term`
- [ ] `test_search_results_displayed`
- [ ] `test_user_clicks_recipe_to_view_details`
- [ ] `test_recipe_details_page_loads`
- [ ] `test_user_saves_recipe_to_profile`
- [ ] `test_user_generates_ai_recipe_from_pantry_items`
- [ ] `test_user_inputs_available_ingredients`
- [ ] `test_ai_generates_recipe_suggestions`
- [ ] `test_user_selects_generated_recipe`

---

### `test_user_journey_shopping_collaboration.py` - Shopping Collaboration Journey

#### TestShoppingCollaborationJourney
- [ ] `test_user_creates_list_invites_collaborator_realtime_sync`
- [ ] `test_user_creates_new_shopping_list`
- [ ] `test_user_adds_items_to_list`
- [ ] `test_user_generates_share_link`
- [ ] `test_user_sends_share_link_to_collaborator`
- [ ] `test_collaborator_joins_via_share_link`
- [ ] `test_collaborator_sees_realtime_updates`
- [ ] `test_collaborator_checks_items_owner_sees_update_instantly`

---

### `test_user_journey_nutrition_tracking.py` - Nutrition Tracking Journey

#### TestNutritionTrackingJourney
- [ ] `test_user_logs_meals_ai_calculates_macros_views_dashboard`
- [ ] `test_user_navigates_to_nutrition_page`
- [ ] `test_user_logs_meal_with_natural_language`
- [ ] `test_ai_parses_meal_and_calculates_macros`
- [ ] `test_meal_logged_successfully`
- [ ] `test_user_views_nutrition_dashboard`
- [ ] `test_dashboard_shows_daily_summary`
- [ ] `test_dashboard_shows_streak_info`

---

## 📁 10. PERFORMANCE TESTS (`tests/performance/`)

### `test_api_response_times.py` - API Response Times

#### TestAPIPerformance
- [ ] `test_recipe_list_api_response_under_200ms`
- [ ] `test_recipe_detail_api_response_under_300ms`
- [ ] `test_recipe_detail_with_cached_translation_under_100ms`
- [ ] `test_shopping_list_api_response_under_200ms`
- [ ] `test_shopping_list_realtime_update_broadcast_under_100ms`
- [ ] `test_nutrition_dashboard_api_response_under_500ms`
- [ ] `test_search_api_response_under_300ms`

---

### `test_cache_performance.py` - Cache Performance

#### TestCachePerformance
- [ ] `test_translation_cache_hit_response_under_50ms`
- [ ] `test_translation_cache_miss_triggers_async_job`
- [ ] `test_discovery_cache_serves_100_pages_under_1s`
- [ ] `test_redis_vs_postgres_cache_performance_comparison`
- [ ] `test_cache_hit_rate_above_80_percent`
- [ ] `test_iml_cache_lookup_performance`
- [ ] `test_cooklingo_cache_lookup_performance`

---

### `test_websocket_load.py` - WebSocket Load

#### TestWebSocketLoad
- [ ] `test_100_concurrent_websocket_connections_stable`
- [ ] `test_websocket_message_broadcast_latency_under_100ms`
- [ ] `test_broadcast_to_1000_users_under_2s`
- [ ] `test_websocket_reconnection_handling`
- [ ] `test_websocket_memory_usage_stable_over_time`

---

### `test_translation_throughput.py` - Translation Throughput

#### TestTranslationThroughput
- [ ] `test_translate_100_recipes_parallel_under_5min`
- [ ] `test_iml_cache_hit_rate_above_80_percent`
- [ ] `test_cooklingo_cache_hit_rate_above_70_percent`
- [ ] `test_gemini_api_calls_per_minute_within_quota`
- [ ] `test_groq_api_calls_per_minute_within_quota`
- [ ] `test_concurrent_translation_requests_handled`

---

## 📁 11. SECURITY TESTS (`tests/security/`)

### `test_authentication_security.py` - Authentication Security

#### TestAuthenticationSecurity
- [ ] `test_jwt_token_tampering_detected_and_rejected`
- [ ] `test_expired_access_token_rejected_with_401`
- [ ] `test_token_replay_attack_prevention`
- [ ] `test_brute_force_login_rate_limiting_after_5_attempts`
- [ ] `test_account_lockout_after_10_failed_attempts`
- [ ] `test_password_hashing_uses_bcrypt_or_argon2`
- [ ] `test_password_minimum_strength_enforced`
- [ ] `test_session_fixation_prevention`

---

### `test_authorization_security.py` - Authorization Security

#### TestAuthorizationSecurity
- [ ] `test_user_cannot_access_other_users_recipes`
- [ ] `test_user_cannot_modify_other_users_recipes`
- [ ] `test_user_cannot_access_other_users_shopping_lists`
- [ ] `test_user_cannot_modify_other_users_shopping_lists`
- [ ] `test_user_cannot_delete_other_users_data`
- [ ] `test_permission_escalation_prevented`
- [ ] `test_horizontal_privilege_escalation_prevented`
- [ ] `test_vertical_privilege_escalation_prevented`

---

### `test_sql_injection.py` - SQL Injection Prevention

#### TestSQLInjectionPrevention
- [ ] `test_search_query_sql_injection_prevented`
- [ ] `test_filter_parameter_sql_injection_prevented`
- [ ] `test_ordering_parameter_sql_injection_prevented`
- [ ] `test_orm_parameterized_queries_used`
- [ ] `test_raw_sql_queries_sanitized`

---

### `test_xss_protection.py` - XSS Protection

#### TestXSSProtection
- [ ] `test_recipe_name_xss_script_sanitized`
- [ ] `test_recipe_description_xss_script_sanitized`
- [ ] `test_comment_xss_script_sanitized`
- [ ] `test_user_profile_fields_xss_sanitized`
- [ ] `test_shopping_list_name_xss_sanitized`
- [ ] `test_html_output_escaped`
- [ ] `test_json_responses_content_type_correct`

---

### `test_rate_limiting.py` - Rate Limiting

#### TestRateLimiting
- [ ] `test_api_rate_limiting_enforced_per_user`
- [ ] `test_api_rate_limit_100_requests_per_minute`
- [ ] `test_login_rate_limiting_5_attempts_per_minute`
- [ ] `test_registration_rate_limiting_3_per_hour`
- [ ] `test_email_sending_rate_limited_to_prevent_spam`
- [ ] `test_rate_limit_headers_included_in_response`
- [ ] `test_rate_limit_exceeded_returns_429`

---

## 📁 12. CELERY TESTS (`tests/celery/`)

### `test_translation_tasks.py` - Translation Tasks

#### TestTranslationTasks
- [ ] `test_translate_recipe_task_success_updates_status`
- [ ] `test_translate_recipe_task_processes_all_languages`
- [ ] `test_translate_recipe_task_retry_on_temporary_failure`
- [ ] `test_translate_recipe_task_max_retries_3`
- [ ] `test_translate_recipe_task_stores_error_on_permanent_failure`
- [ ] `test_translation_task_updates_database_record`
- [ ] `test_translation_task_caches_result`

---

### `test_discovery_cache_tasks.py` - Discovery Cache Tasks

#### TestDiscoveryCacheTasks
- [ ] `test_refresh_discovery_cache_task_updates_all_languages`
- [ ] `test_refresh_discovery_cache_task_updates_redis`
- [ ] `test_refresh_discovery_cache_task_updates_postgres`
- [ ] `test_cache_refresh_scheduled_by_celery_beat_hourly`
- [ ] `test_cache_refresh_handles_errors_gracefully`

---

### `test_cleanup_tasks.py` - Cleanup Tasks

#### TestCleanupTasks
- [ ] `test_cleanup_expired_share_keys_deletes_old_keys`
- [ ] `test_cleanup_expired_share_keys_scheduled_daily`
- [ ] `test_cleanup_old_translation_failures_older_than_7_days`
- [ ] `test_cleanup_archived_lists_older_than_30_days`
- [ ] `test_cleanup_stale_discovery_cache_older_than_24_hours`

---

### `test_task_scheduling.py` - Task Scheduling

#### TestTaskScheduling
- [ ] `test_celery_beat_schedules_hourly_translation_refresh`
- [ ] `test_celery_beat_schedules_daily_cleanup`
- [ ] `test_celery_beat_schedules_weekly_analytics_generation`
- [ ] `test_scheduled_tasks_run_at_correct_intervals`
- [ ] `test_task_schedule_configuration_loaded_correctly`

---

## 📊 Summary Statistics

**Total Test Count: ~450+**

### By App:
- Users: ~70 tests
- Recipes: ~110 tests
- Shopping: ~75 tests
- Nutrition: ~35 tests
- Core: ~55 tests
- AI Agents: ~45 tests
- Legal: ~25 tests
- Integration: ~15 tests
- E2E: ~15 tests
- Performance: ~15 tests
- Security: ~25 tests
- Celery: ~15 tests

### By Type:
- Unit Tests: ~270 (60%)
- Integration Tests: ~135 (30%)
- E2E Tests: ~15 (3%)
- Performance Tests: ~15 (3%)
- Security Tests: ~25 (6%)

---

## 📝 Usage Notes

**This checklist provides:**
1. ✅ Complete test names ready to implement
2. ✅ Organized by app and test file
3. ✅ Checkbox format for tracking progress
4. ✅ Descriptive names following best practices
5. ✅ Coverage of all critical paths

**Implementation strategy:**
- Start with Users app
- Then Core/AI Agents (dependencies)
- Then feature apps (Recipes, Shopping, Nutrition)
- Finally integration, E2E, performance, security

**Each test name indicates:**
- What is being tested
- Expected behavior/outcome
- Clear pass/fail criteria

---

**Ready to start implementation!** 🚀
