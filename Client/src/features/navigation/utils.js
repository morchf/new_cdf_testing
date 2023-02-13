/**
 * Replenish id token from local storage after hard refresh
 * @case Amplify and Auth async calls cause occasional timeouts and other undesired behavior.
 * @returns encoded Cognito JWT id token
 */
export const getStoredToken = () => {
  const keys = Object.keys(localStorage);
  for (let i = 0; i < keys.length; i++) {
    const match = keys[i].match(new RegExp('idToken'));
    const idToken = !match ? null : localStorage.getItem(match.input);
    if (idToken) return idToken;
  }
  return null;
};
