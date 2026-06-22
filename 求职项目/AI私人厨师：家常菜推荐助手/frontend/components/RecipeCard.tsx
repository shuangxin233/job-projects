import { Recipe } from "@/types/chat";
import { ChefHat, Clock, ExternalLink } from "lucide-react";

interface RecipeCardProps {
  recipe: Recipe;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const getScoreColor = (score: number | undefined) => {
    if (score === undefined) return "bg-stone-400";
    if (score >= 4) return "bg-emerald-600";
    if (score >= 3) return "bg-orange-600";
    return "bg-red-600";
  };

  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4 transition hover:shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-lg font-semibold text-stone-900">{recipe.title}</h3>
            {recipe.score !== undefined && (
              <span className={`${getScoreColor(recipe.score)} rounded-full px-2 py-1 text-xs text-white`}>
                {recipe.score}/5
              </span>
            )}
          </div>
          {recipe.reason && <p className="mb-2 text-sm text-stone-600">{recipe.reason}</p>}
          {recipe.difficulty && (
            <div className="flex items-center gap-1 text-sm text-stone-500">
              <ChefHat size={14} />
              <span>{recipe.difficulty}</span>
            </div>
          )}
        </div>
        {recipe.url && (
          <a
            href={recipe.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-500 hover:text-orange-600"
            aria-label="打开菜谱来源"
          >
            <ExternalLink size={20} />
          </a>
        )}
      </div>

      {recipe.steps && recipe.steps.length > 0 && (
        <div className="mt-3">
          <h4 className="mb-1 text-sm font-medium text-stone-900">制作步骤</h4>
          <ul className="list-inside list-disc space-y-1 text-sm text-stone-600">
            {recipe.steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {recipe.seasonings && recipe.seasonings.length > 0 && (
        <div className="mt-3">
          <h4 className="mb-1 text-sm font-medium text-stone-900">所需调料</h4>
          <p className="text-sm text-stone-600">{recipe.seasonings.join(", ")}</p>
        </div>
      )}

      {recipe.cooking_time && (
        <div className="mt-3 flex items-center gap-1 text-sm text-stone-500">
          <Clock size={14} />
          <span>{recipe.cooking_time}</span>
        </div>
      )}
    </div>
  );
}
