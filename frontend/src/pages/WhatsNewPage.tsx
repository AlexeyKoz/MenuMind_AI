import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Alert,
    Divider,
    Stack,
    Paper
} from '@mui/material';
import {
    NewReleases as NewIcon,
    Schedule as UpcomingIcon,
    CheckCircle as CompletedIcon,
    Star as FeaturedIcon
} from '@mui/icons-material';

interface AppUpdate {
    id: string;
    title: string;
    description: string;
    status: 'completed' | 'upcoming';
    version: string | null;
    publish_date: string;
    is_featured: boolean;
    language: string;
}

const WhatsNewPage: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [updates, setUpdates] = useState<AppUpdate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchUpdates();
    }, [i18n.language]);

    const fetchUpdates = async () => {
        try {
            setLoading(true);
            setError(null);

            // Normalize language (ru-RU -> ru, en-US -> en, he-IL -> he)
            const rawLang = i18n.language || 'en';
            const language = rawLang.split('-')[0];
            
            // Direct URL to backend (bypass proxy)
            const response = await axios.get('http://localhost:8000/api/updates/', {
                params: {
                    language: language,
                    limit: 50
                }
            });

            if (response.data.success) {
                setUpdates(response.data.updates);
            }
        } catch (err) {
            console.error('Failed to fetch updates:', err);
            setError(t('Failed to load updates. Please try again later.'));
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (status: string) => {
        return status === 'completed' ? (
            <CompletedIcon sx={{ color: 'success.main', mr: 1 }} />
        ) : (
            <UpcomingIcon sx={{ color: 'info.main', mr: 1 }} />
        );
    };

    const getStatusColor = (status: string): 'success' | 'info' => {
        return status === 'completed' ? 'success' : 'info';
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString(i18n.language, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    if (loading) {
        return (
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
                <CircularProgress />
                <Typography sx={{ mt: 2 }}>{t('Loading updates...')}</Typography>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            {/* Header */}
            <Box sx={{ mb: 4 }}>
                <Typography
                    variant="h3"
                    component="h1"
                    gutterBottom
                    sx={{
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2
                    }}
                >
                    <NewIcon sx={{ fontSize: '2.5rem', color: 'primary.main' }} />
                    {t("What's New")}
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                    {t('Stay up to date with the latest features and improvements')}
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {updates.length === 0 && !error && (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                    <NewIcon sx={{ fontSize: '4rem', color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                        {t('No updates available yet')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('Check back soon for new features and improvements!')}
                    </Typography>
                </Paper>
            )}

            {/* Updates List */}
            <Stack spacing={3}>
                {updates.map((update) => (
                    <Card
                        key={update.id}
                        elevation={update.is_featured ? 4 : 1}
                        sx={{
                            border: update.is_featured ? 2 : 0,
                            borderColor: update.is_featured ? 'primary.main' : 'transparent',
                            position: 'relative',
                            overflow: 'visible',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                                transform: 'translateY(-4px)',
                                boxShadow: 4
                            }
                        }}
                    >
                        {update.is_featured && (
                            <Box
                                sx={{
                                    position: 'absolute',
                                    top: -12,
                                    right: 20,
                                    bgcolor: 'primary.main',
                                    color: 'white',
                                    px: 2,
                                    py: 0.5,
                                    borderRadius: 2,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 0.5,
                                    fontWeight: 600,
                                    fontSize: '0.875rem',
                                    boxShadow: 2
                                }}
                            >
                                <FeaturedIcon sx={{ fontSize: '1rem' }} />
                                {t('Featured')}
                            </Box>
                        )}

                        <CardContent sx={{ p: 3 }}>
                            {/* Header */}
                            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                                <Box sx={{ flex: 1 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        {getStatusIcon(update.status)}
                                        <Typography variant="h5" component="h2" sx={{ fontWeight: 600 }}>
                                            {update.title}
                                        </Typography>
                                    </Box>

                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                                        <Chip
                                            label={update.status === 'completed' ? t('Completed') : t('Upcoming')}
                                            color={getStatusColor(update.status)}
                                            size="small"
                                        />
                                        {update.version && (
                                            <Chip
                                                label={`v${update.version}`}
                                                variant="outlined"
                                                size="small"
                                            />
                                        )}
                                        <Typography variant="caption" color="text.secondary">
                                            {formatDate(update.publish_date)}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Box>

                            <Divider sx={{ my: 2 }} />

                            {/* Description */}
                            <Typography
                                variant="body1"
                                color="text.primary"
                                sx={{
                                    whiteSpace: 'pre-line',
                                    lineHeight: 1.7
                                }}
                            >
                                {update.description}
                            </Typography>
                        </CardContent>
                    </Card>
                ))}
            </Stack>
        </Container>
    );
};

export default WhatsNewPage;

